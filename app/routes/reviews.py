from flask import Blueprint, abort, g, redirect, render_template, request, url_for
from app.extensions import db
from app.models import Product, Review
from app.services.security import login_required
from app.logging_config import event

bp = Blueprint("reviews", __name__)


@bp.get("/products/<int:product_id>/reviews")
def index(product_id):
    product = db.get_or_404(Product, product_id)
    reviews = db.session.scalars(db.select(Review).where(Review.product_id == product_id).order_by(Review.id.desc())).all()
    return render_template("reviews.html", product=product, reviews=reviews)


@bp.post("/products/<int:product_id>/reviews")
@login_required
def create(product_id):
    db.get_or_404(Product, product_id)
    content = request.form.get("content", "").strip()
    if not 1 <= len(content) <= 2000:
        abort(400)
    db.session.add(Review(user_id=g.user.id, product_id=product_id, content=content))
    db.session.commit()
    event("REVIEW_CREATED", 303)
    return redirect(url_for("reviews.index", product_id=product_id), code=303)
