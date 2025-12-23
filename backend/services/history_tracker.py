import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from config import settings
from utils.redis import redis_cache


class ActivityType(Enum):
    """活动类型枚举"""
    INTERVIEW = "interview"
    EXAM = "exam" 
    QNA = "qna"
    UPLOAD = "upload"
    REPORT = "report"


@dataclass
class ActivityRecord:
    """活动记录数据类"""
    user_id: str
    activity_type: ActivityType
    timestamp: datetime.datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class UserHistoryTracker:
    """用户历史追踪器"""
    
    def __init__(self):
        self.redis_prefix = "user_history"
    
    def record_activity(self, user_id: str, activity_type: ActivityType, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """记录用户活动
        
        Args:
            user_id: 用户ID
            activity_type: 活动类型
            data: 活动数据
            metadata: 元数据（可选）
            
        Returns:
            是否记录成功
        """
        try:
            # 创建活动记录
            record = ActivityRecord(
                user_id=user_id,
                activity_type=activity_type,
                timestamp=datetime.datetime.now(),
                data=data,
                metadata=metadata or {}
            )
            
            # 转换为可序列化的字典
            record_dict = {
                "user_id": record.user_id,
                "activity_type": record.activity_type.value,
                "timestamp": record.timestamp.isoformat(),
                "data": record.data,
                "metadata": record.metadata
            }
            
            # 生成唯一键
            key = f"{self.redis_prefix}:{user_id}:{record.timestamp.strftime('%Y%m%d%H%M%S')}"
            
            # 存储到Redis（过期时间30天）
            redis_cache.set(key, json.dumps(record_dict), expire=30 * 24 * 60 * 60)
            
            # 更新用户活动索引
            self._update_user_activity_index(user_id, key, activity_type)
            
            return True
            
        except Exception as e:
            print(f"记录活动失败: {e}")
            return False
    
    def get_user_activities(self, user_id: str, activity_type: Optional[ActivityType] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户活动记录
        
        Args:
            user_id: 用户ID
            activity_type: 活动类型过滤（可选）
            limit: 返回记录数量限制
            
        Returns:
            活动记录列表
        """
        try:
            # 获取用户活动索引
            index_key = f"{self.redis_prefix}:index:{user_id}"
            activity_keys = redis_cache.lrange(index_key, 0, limit - 1)
            
            activities = []
            for key in activity_keys:
                activity_data = redis_cache.get(key)
                if activity_data:
                    activity = json.loads(activity_data)
                    
                    # 过滤活动类型
                    if activity_type and activity["activity_type"] != activity_type.value:
                        continue
                    
                    activities.append(activity)
            
            # 按时间倒序排序
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return activities[:limit]
            
        except Exception as e:
            print(f"获取用户活动失败: {e}")
            return []
    
    def get_activity_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户活动统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            活动统计信息
        """
        try:
            activities = self.get_user_activities(user_id)
            
            # 按类型统计
            type_counts = {}
            total_time_spent = 0
            total_questions = 0
            
            for activity in activities:
                activity_type = activity["activity_type"]
                type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
                
                # 统计时间和问题数量
                data = activity["data"]
                if "time_spent" in data:
                    total_time_spent += data["time_spent"]
                if "question_count" in data:
                    total_questions += data["question_count"]
            
            return {
                "total_activities": len(activities),
                "type_counts": type_counts,
                "total_time_spent": total_time_spent,
                "total_questions": total_questions,
                "first_activity": activities[-1]["timestamp"] if activities else None,
                "last_activity": activities[0]["timestamp"] if activities else None
            }
            
        except Exception as e:
            print(f"获取活动统计失败: {e}")
            return {"total_activities": 0, "type_counts": {}, "total_time_spent": 0, "total_questions": 0}
    
    def get_progress_trend(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取用户进度趋势
        
        Args:
            user_id: 用户ID
            days: 天数范围
            
        Returns:
            进度趋势数据
        """
        try:
            activities = self.get_user_activities(user_id)
            
            # 按日期分组
            daily_stats = {}
            today = datetime.datetime.now().date()
            
            for activity in activities:
                activity_date = datetime.datetime.fromisoformat(activity["timestamp"][:10]).date()
                
                # 只统计指定天数内的数据
                if (today - activity_date).days > days:
                    continue
                
                date_str = activity_date.isoformat()
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "date": date_str,
                        "activities": 0,
                        "time_spent": 0,
                        "questions": 0,
                        "scores": []
                    }
                
                stats = daily_stats[date_str]
                stats["activities"] += 1
                
                data = activity["data"]
                if "time_spent" in data:
                    stats["time_spent"] += data["time_spent"]
                if "question_count" in data:
                    stats["questions"] += data["question_count"]
                if "score" in data:
                    stats["scores"].append(data["score"])
            
            # 计算每日平均分
            for stats in daily_stats.values():
                if stats["scores"]:
                    stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])
                else:
                    stats["avg_score"] = 0
                stats.pop("scores", None)
            
            # 按日期排序
            trend_data = sorted(daily_stats.values(), key=lambda x: x["date"])
            
            return {
                "days": days,
                "trend_data": trend_data,
                "summary": self._calculate_trend_summary(trend_data)
            }
            
        except Exception as e:
            print(f"获取进度趋势失败: {e}")
            return {"days": days, "trend_data": [], "summary": {}}
    
    def get_weak_areas_analysis(self, user_id: str) -> Dict[str, Any]:
        """获取用户薄弱环节分析
        
        Args:
            user_id: 用户ID
            
        Returns:
            薄弱环节分析
        """
        try:
            activities = self.get_user_activities(user_id)
            
            weak_areas = {}
            strong_areas = {}
            
            for activity in activities:
                data = activity["data"]
                
                # 分析薄弱环节
                if "weak_areas" in data:
                    for area in data["weak_areas"]:
                        weak_areas[area] = weak_areas.get(area, 0) + 1
                
                # 分析优势领域
                if "strong_areas" in data:
                    for area in data["strong_areas"]:
                        strong_areas[area] = strong_areas.get(area, 0) + 1
            
            # 排序并取前5个
            top_weak = sorted(weak_areas.items(), key=lambda x: x[1], reverse=True)[:5]
            top_strong = sorted(strong_areas.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "top_weak_areas": [{"area": area, "count": count} for area, count in top_weak],
                "top_strong_areas": [{"area": area, "count": count} for area, count in top_strong],
                "improvement_priority": self._calculate_improvement_priority(top_weak, top_strong)
            }
            
        except Exception as e:
            print(f"获取薄弱环节分析失败: {e}")
            return {"top_weak_areas": [], "top_strong_areas": [], "improvement_priority": []}
    
    def clear_user_history(self, user_id: str) -> bool:
        """清除用户历史记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否清除成功
        """
        try:
            # 获取所有用户活动键
            index_key = f"{self.redis_prefix}:index:{user_id}"
            activity_keys = redis_cache.lrange(index_key, 0, -1)
            
            # 删除所有活动记录
            for key in activity_keys:
                redis_cache.delete(key)
            
            # 删除索引
            redis_cache.delete(index_key)
            
            return True
            
        except Exception as e:
            print(f"清除用户历史失败: {e}")
            return False
    
    def _update_user_activity_index(self, user_id: str, activity_key: str, activity_type: ActivityType):
        """更新用户活动索引"""
        try:
            index_key = f"{self.redis_prefix}:index:{user_id}"
            
            # 添加到列表头部
            redis_cache.lpush(index_key, activity_key)
            
            # 限制列表长度（最多1000条记录）
            redis_cache.ltrim(index_key, 0, 999)
            
        except Exception as e:
            print(f"更新用户活动索引失败: {e}")
    
    def _calculate_trend_summary(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算趋势摘要"""
        if not trend_data:
            return {}
        
        # 计算平均值
        avg_activities = sum(d["activities"] for d in trend_data) / len(trend_data)
        avg_time = sum(d["time_spent"] for d in trend_data) / len(trend_data)
        avg_questions = sum(d["questions"] for d in trend_data) / len(trend_data)
        
        # 计算趋势
        recent_activities = sum(d["activities"] for d in trend_data[-7:]) if len(trend_data) >= 7 else sum(d["activities"] for d in trend_data)
        previous_activities = sum(d["activities"] for d in trend_data[-14:-7]) if len(trend_data) >= 14 else 0
        
        trend = "stable"
        if previous_activities > 0:
            trend_change = (recent_activities - previous_activities) / previous_activities * 100
            if trend_change > 10:
                trend = "increasing"
            elif trend_change < -10:
                trend = "decreasing"
        
        return {
            "avg_daily_activities": round(avg_activities, 1),
            "avg_daily_time": round(avg_time, 1),
            "avg_daily_questions": round(avg_questions, 1),
            "activity_trend": trend
        }
    
    def _calculate_improvement_priority(self, weak_areas: List, strong_areas: List) -> List[str]:
        """计算改进优先级"""
        priorities = []
        
        # 根据薄弱环节的出现频率和重要性排序
        for area, count in weak_areas:
            # 简单优先级算法：频率越高，优先级越高
            priorities.append(area)
        
        return priorities[:5]


def get_history_tracker() -> UserHistoryTracker:
    """获取历史追踪器实例"""
    return UserHistoryTracker()