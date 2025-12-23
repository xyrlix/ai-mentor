from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import stripe
from typing import Dict, Any

from config import settings
from models import User
from routes.auth import get_current_active_user

router = APIRouter(prefix="/api/payment", tags=["支付"])

# 初始化Stripe客户端
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY


@router.get("/prices")
async def get_prices(current_user: User = Depends(get_current_active_user)):
    """获取可用的价格列表"""
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="支付系统未配置")

    try:
        prices = stripe.Price.list(active=True, limit=10)
        return {"status": "success", "prices": prices.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取价格失败: {str(e)}")


@router.post("/create-checkout-session")
async def create_checkout_session(
        current_user: User = Depends(get_current_active_user)):
    """创建结账会话"""
    if not settings.STRIPE_API_KEY or not settings.STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="支付系统未配置")

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            client_reference_id=str(current_user.id),
        )

        return {
            "status": "success",
            "session_url": checkout_session.url,
            "session_id": checkout_session.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建结账会话失败: {str(e)}")


@router.post("/webhook")
async def webhook_received(request: Request):
    """处理Stripe Webhook事件"""
    if not settings.STRIPE_API_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="支付系统未配置")

    event = None
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header,
                                               settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # 无效的负载
        raise HTTPException(status_code=400, detail=f"无效的负载: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        # 无效的签名
        raise HTTPException(status_code=400, detail=f"无效的签名: {str(e)}")

    # 处理事件
    if event.type == "checkout.session.completed":
        session = event.data.object
        # 处理成功的结账会话
        user_id = session.client_reference_id
        subscription_id = session.subscription
        # 这里可以更新用户的订阅状态
        print(f"用户 {user_id} 订阅成功，订阅ID: {subscription_id}")

    elif event.type == "invoice.paid":
        invoice = event.data.object
        # 处理成功的发票支付
        subscription_id = invoice.subscription
        print(f"订阅 {subscription_id} 支付成功")

    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        # 处理失败的发票支付
        subscription_id = invoice.subscription
        print(f"订阅 {subscription_id} 支付失败")

    return JSONResponse(content={"status": "success"})


@router.get("/subscription-status")
async def get_subscription_status(
        current_user: User = Depends(get_current_active_user)):
    """获取当前用户的订阅状态"""
    # 这里可以查询数据库获取用户的订阅状态
    # 简化实现，返回默认状态
    return {
        "status": "success",
        "subscription": {
            "status": "active",
            "plan": "free",
            "expires_at": None
        }
    }
