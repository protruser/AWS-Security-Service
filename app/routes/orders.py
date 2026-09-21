from flask import Blueprint, abort, g, redirect, render_template, request, url_for
from app.extensions import db
from app.models import Order, OrderItem, Product
from app.services.security import login_required
from app.logging_config import event

bp = Blueprint("orders", __name__)


@bp.get("/orders")
@login_required
def index():
    orders = db.session.scalars(db.select(Order).where(Order.user_id == g.user.id).order_by(Order.id.desc())).all()
    return render_template("orders.html", orders=orders)


@bp.post("/orders")
@login_required
def create():
    try:
        product_id = int(request.form.get("product_id", ""))
        quantity = int(request.form.get("quantity", ""))
    except ValueError:
        abort(400)
    if product_id <= 0 or not 1 <= quantity <= 100:
        abort(400)
    product = db.session.scalar(db.select(Product).where(Product.id == product_id).with_for_update())
    if product is None:
        db.session.rollback()
        abort(404)
    if product.stock < quantity:
        db.session.rollback()
        event("INPUT_VALIDATION_FAILED", 409)
        return render_template("error.html", code=409), 409
    product.stock -= quantity
    order = Order(user_id=g.user.id, total_price=product.price * quantity)
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, price=product.price))
    db.session.commit()
    event("ORDER_CREATED", 303)
    return redirect(url_for("orders.index"), code=303)
