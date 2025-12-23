import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random


class QuestionSpider:
    """面试题爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
    
    def crawl_lc_questions(self, tag: str = "python", page: int = 1) -> List[Dict]:
        """爬取力扣面试题
        
        Args:
            tag: 标签，如python、java等
            page: 页码
        
        Returns:
            面试题列表
        """
        questions = []
        url = f"https://leetcode.cn/problemset/all/?topicSlugs={tag}&page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            question_list = soup.find_all('div', class_='question-list-item')
            
            for item in question_list:
                # 提取题目信息
                title_elem = item.find('a', class_='title')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem['href']
                difficulty_elem = item.find('span', class_='difficulty')
                difficulty = difficulty_elem.text.strip() if difficulty_elem else '未知'
                
                questions.append({
                    'title': title,
                    'link': f"https://leetcode.cn{link}",
                    'difficulty': difficulty,
                    'source': 'leetcode',
                    'tag': tag
                })
            
            return questions
        except Exception as e:
            print(f"爬取力扣题目失败: {e}")
            return []
    
    def crawl_nowcoder_questions(self, category: str = "computer-science", page: int = 1) -> List[Dict]:
        """爬取牛客网面试题
        
        Args:
            category: 分类
            page: 页码
        
        Returns:
            面试题列表
        """
        questions = []
        url = f"https://www.nowcoder.com/intelligentTest/questionList?type=0&tagId={category}&page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 牛客网使用动态加载，可能需要处理JavaScript渲染
            # 这里简化处理，实际项目中可能需要使用Selenium或分析API
            soup = BeautifulSoup(response.text, 'html.parser')
            # 具体的选择器需要根据实际页面结构调整
            question_list = soup.find_all('div', class_='question-item')
            
            for item in question_list:
                title_elem = item.find('a', class_='question-title')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem['href']
                
                questions.append({
                    'title': title,
                    'link': link,
                    'source': 'nowcoder',
                    'category': category
                })
            
            return questions
        except Exception as e:
            print(f"爬取牛客网题目失败: {e}")
            return []
    
    def crawl_zhihu_articles(self, topic: str = "面试经验", page: int = 1) -> List[Dict]:
        """爬取知乎面试相关文章
        
        Args:
            topic: 话题
            page: 页码
        
        Returns:
            文章列表
        """
        articles = []
        url = f"https://www.zhihu.com/search?q={topic}&type=content&page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            article_list = soup.find_all('div', class_='SearchResult-Card')
            
            for item in article_list:
                title_elem = item.find('h2', class_='ContentItem-title')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link_elem = title_elem.find('a')
                link = link_elem['href'] if link_elem else ''
                
                articles.append({
                    'title': title,
                    'link': link,
                    'source': 'zhihu',
                    'topic': topic
                })
            
            return articles
        except Exception as e:
            print(f"爬取知乎文章失败: {e}")
            return []
    
    def crawl_questions(self, sources: List[str] = None, tags: List[str] = None, pages: int = 1) -> List[Dict]:
        """爬取多个来源的面试题
        
        Args:
            sources: 来源列表，如['leetcode', 'nowcoder', 'zhihu']
            tags: 标签列表
            pages: 爬取的页数
        
        Returns:
            合并后的面试题列表
        """
        all_questions = []
        sources = sources or ['leetcode', 'nowcoder']
        tags = tags or ['python', 'java']
        
        for source in sources:
            for tag in tags:
                for page in range(1, pages + 1):
                    if source == 'leetcode':
                        questions = self.crawl_lc_questions(tag, page)
                    elif source == 'nowcoder':
                        questions = self.crawl_nowcoder_questions(tag, page)
                    elif source == 'zhihu':
                        questions = self.crawl_zhihu_articles(tag, page)
                    else:
                        questions = []
                    
                    all_questions.extend(questions)
                    # 随机休眠，避免被封IP
                    time.sleep(random.uniform(1, 3))
        
        return all_questions
    
    def save_questions(self, questions: List[Dict], file_path: str):
        """保存面试题到文件
        
        Args:
            questions: 面试题列表
            file_path: 保存路径
        """
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(questions)} 道面试题到 {file_path}")
