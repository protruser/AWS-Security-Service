from flask import Blueprint, abort, current_app, render_template, request
from sqlalchemy.exc import SQLAlchemyError
from app.services.lab import suspicious_search, vulnerable_search
from app.extensions import db
from app.models import Product
from app.logging_config import event

bp = Blueprint("products", __name__)


@bp.get("/")
@bp.get("/products")
def index():
    products = db.session.scalars(db.select(Product).order_by(Product.id)).all()
    return render_template("products.html", products=products, query=None)


@bp.get("/search")
def search():
    query = request.args.get("q", "").strip()
    suspicious = suspicious_search(query)
    if len(query) > 120:
        if suspicious:
            event("SUSPICIOUS_SEARCH_INPUT", 400)
        abort(400)
    try:
        if current_app.config["VULNERABLE_LAB"]:
            products = vulnerable_search(query)
        else:
            products = db.session.scalars(db.select(Product).where(
                Product.name.contains(query, autoescape=True)).order_by(Product.id)).all()
    except SQLAlchemyError:
        db.session.rollback()
        if suspicious:
            event("SUSPICIOUS_SEARCH_INPUT", 503)
        event("DATABASE_QUERY_ERROR", 503)
        return render_template("error.html", code=503), 503
    if suspicious:
        event("SUSPICIOUS_SEARCH_INPUT")
    event("PRODUCT_SEARCH")
    return render_template("products.html", products=products, query=query)


@bp.get("/products/<int:product_id>")
def detail(product_id):
    product = db.get_or_404(Product, product_id)
    event("PRODUCT_VIEWED")
    return render_template("product.html", product=product)
