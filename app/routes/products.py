from flask import Blueprint, abort, render_template, request
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
    if len(query) > 120:
        abort(400)
    products = db.session.scalars(db.select(Product).where(
        Product.name.contains(query, autoescape=True)).order_by(Product.id)).all()
    event("PRODUCT_SEARCH")
    return render_template("products.html", products=products, query=query)


@bp.get("/products/<int:product_id>")
def detail(product_id):
    product = db.get_or_404(Product, product_id)
    event("PRODUCT_VIEWED")
    return render_template("product.html", product=product)
