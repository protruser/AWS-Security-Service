from decimal import Decimal, InvalidOperation
import re

from flask import Blueprint, abort, redirect, render_template, request, url_for
from app.extensions import db
from app.models import Product
from app.services.security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/management")


def stock_value():
    value = request.form.get("stock", "").strip()
    if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) > 2147483647:
        abort(400)
    return int(value)


def product_values():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not 1 <= len(name) <= 120 or not description:
        abort(400)
    try:
        price = Decimal(request.form.get("price", ""))
        if (not price.is_finite() or not 0 <= price <= Decimal("99999999.99")
                or price != price.quantize(Decimal("0.01"))):
            abort(400)
    except InvalidOperation:
        abort(400)
    return dict(name=name, description=description, price=price, stock=stock_value())


def locked_product(product_id):
    product = db.session.scalar(db.select(Product).where(Product.id == product_id)
                                .with_for_update().execution_options(populate_existing=True))
    if product is None:
        db.session.rollback()
        abort(404)
    return product


@bp.get("/products")
@admin_required
def products():
    items = db.session.scalars(db.select(Product).order_by(Product.id)).all()
    return render_template("admin/products.html", products=items)


@bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def new():
    if request.method == "POST":
        db.session.add(Product(**product_values()))
        db.session.commit()
        return redirect(url_for("admin.products"), code=303)
    return render_template("admin/product_form.html", product=None)


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(product_id):
    if request.method == "POST":
        product = locked_product(product_id)
        values = product_values()
        for key, value in values.items():
            setattr(product, key, value)
        db.session.commit()
        return redirect(url_for("admin.products"), code=303)
    return render_template("admin/product_form.html", product=db.get_or_404(Product, product_id))


@bp.post("/products/<int:product_id>/stock")
@admin_required
def stock(product_id):
    product = locked_product(product_id)
    product.stock = stock_value()
    db.session.commit()
    return redirect(url_for("admin.products"), code=303)
