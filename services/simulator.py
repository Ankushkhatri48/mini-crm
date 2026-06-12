import random
from datetime import datetime
from database.db import get_session
from database.models import Campaign, CommunicationLog, Customer, Segment
import json


STATUS_WEIGHTS = {
    "Delivered": 0.30,
    "Opened": 0.35,
    "Clicked": 0.25,
    "Failed": 0.10,
}


def get_segment_customers(segment: Segment) -> list[Customer]:
    db = get_session()
    try:
        rules = json.loads(segment.rules)
        query = db.query(Customer)

        if "min_spend" in rules:
            query = query.filter(Customer.total_spend >= rules["min_spend"])
        if "max_spend" in rules:
            query = query.filter(Customer.total_spend <= rules["max_spend"])
        if "min_orders" in rules:
            query = query.filter(Customer.total_orders >= rules["min_orders"])
        if "max_orders" in rules:
            query = query.filter(Customer.total_orders <= rules["max_orders"])
        if "city" in rules:
            query = query.filter(Customer.city.ilike(rules["city"]))

        return query.all()
    finally:
        db.close()


def simulate_campaign(campaign_id: int) -> dict:
    db = get_session()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"error": "Campaign not found"}

        customers = get_segment_customers(campaign.segment)
        if not customers:
            return {"error": "No customers in segment"}

        statuses = list(STATUS_WEIGHTS.keys())
        weights = list(STATUS_WEIGHTS.values())
        counts = {"Delivered": 0, "Opened": 0, "Clicked": 0, "Failed": 0}

        for customer in customers:
            status = random.choices(statuses, weights=weights, k=1)[0]
            log = CommunicationLog(
                campaign_id=campaign_id,
                customer_id=customer.id,
                status=status,
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            counts[status] += 1

        db.commit()
        return {"success": True, "total": len(customers), "counts": counts}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def get_campaign_stats(campaign_id: int) -> dict:
    db = get_session()
    try:
        logs = db.query(CommunicationLog).filter(
            CommunicationLog.campaign_id == campaign_id
        ).all()

        stats = {"Delivered": 0, "Opened": 0, "Clicked": 0, "Failed": 0, "Total": len(logs)}
        for log in logs:
            stats[log.status] = stats.get(log.status, 0) + 1

        return stats
    finally:
        db.close()
