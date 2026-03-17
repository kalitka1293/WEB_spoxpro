import io
import json
import os
import uuid
from PIL import Image
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from db.database import SessionLocal
from db.products import Product
from config.settings import get_settings

router_images = APIRouter(prefix="/image-manager", tags=["image-manager"])

IMAGES_DIR = get_settings().images_path


def _root(request: Request) -> str:
    return request.scope.get("root_path", "")


def _check_admin(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(f"{_root(request)}/admin/login", status_code=303)
    return None


def _get_images(product):
    if not product.images:
        return []
    if isinstance(product.images, str):
        return json.loads(product.images)
    return list(product.images)


def _serve_url(img):
    return f"{get_settings().images_url_prefix}/{img['file_id']}"


def _render_page(request, product, images, msg=""):
    pid = product.id
    root = _root(request)
    msg_html = f'<div class="alert alert-success mt-2">{msg}</div>' if msg else ""

    imgs_html = ""
    for i, img in enumerate(images):
        url = _serve_url(img)
        fname = img.get("filename", "")
        imgs_html += f'''
        <div class="card d-inline-block m-1" style="width:150px" data-index="{i}">
            <img src="{url}" class="card-img-top" style="height:120px;object-fit:cover">
            <div class="card-body p-1 text-center">
                <small class="text-muted">{fname[:20]}</small>
                <div class="mt-1">
                    <form method="post" action="{root}/image-manager/{pid}/delete" class="d-inline">
                        <input type="hidden" name="index" value="{i}">
                        <button class="btn btn-danger btn-sm">&times;</button>
                    </form>
                    {"" if i == 0 else f'<form method="post" action="{root}/image-manager/{pid}/move" class="d-inline"><input type="hidden" name="from_idx" value="{i}"><input type="hidden" name="to_idx" value="{i-1}"><button class="btn btn-outline-secondary btn-sm">&uarr;</button></form>'}
                    {"" if i == len(images)-1 else f'<form method="post" action="{root}/image-manager/{pid}/move" class="d-inline"><input type="hidden" name="from_idx" value="{i}"><input type="hidden" name="to_idx" value="{i+1}"><button class="btn btn-outline-secondary btn-sm">&darr;</button></form>'}
                </div>
            </div>
        </div>'''

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Изображения - {product.name}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head><body class="bg-light">
<div class="container mt-4" style="max-width:800px">
<h4>Изображения: {product.name} (ID: {pid})</h4>
{msg_html}
<div class="my-3">{imgs_html if imgs_html else '<p class="text-muted">Нет изображений</p>'}</div>
<hr>
<h5>Добавить изображения</h5>
<form method="post" action="{root}/image-manager/{pid}/upload" enctype="multipart/form-data">
<div class="mb-2"><input type="file" name="files" multiple accept="image/*" class="form-control" required></div>
<button type="submit" class="btn btn-primary">Загрузить</button>
</form>
<hr>
<a href="{root}/admin/product/list" class="btn btn-secondary">Назад к товарам</a>
</div></body></html>"""


@router_images.get("/{product_id}", response_class=HTMLResponse)
async def image_manager_page(product_id: int, request: Request):
    redirect = _check_admin(request)
    if redirect:
        return redirect
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return HTMLResponse("Товар не найден", status_code=404)
        images = _get_images(product)
        return HTMLResponse(_render_page(request, product, images))
    finally:
        db.close()


@router_images.post("/{product_id}/upload", response_class=HTMLResponse)
async def upload_images(product_id: int, request: Request):
    redirect = _check_admin(request)
    if redirect:
        return redirect
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return HTMLResponse("Товар не найден", status_code=404)

        images = _get_images(product)
        form = await request.form()
        files = form.getlist("files")
        count = 0

        for f in files:
            if hasattr(f, "filename") and f.filename:
                file_id = str(uuid.uuid4()) + ".webp"
                dest = os.path.join(IMAGES_DIR, file_id)
                contents = await f.read()
                img = Image.open(io.BytesIO(contents))
                img.save(dest, format="WEBP")
                saved_size = os.path.getsize(dest)
                images.append({
                    "filename": f.filename,
                    "content_type": "image/webp",
                    "size": saved_size,
                    "file_id": file_id,
                    "upload_storage": "default",
                    "path": f"default/{file_id}",
                    "files": [f"default/{file_id}"],
                    "saved": True,
                })
                count += 1

        db.expire(product)
        db.execute(text("UPDATE products SET images = :img WHERE id = :pid"),
                   {"img": json.dumps(images), "pid": product_id})
        db.commit()
        return RedirectResponse(f"{_root(request)}/image-manager/{product_id}", status_code=303)
    finally:
        db.close()


@router_images.post("/{product_id}/delete", response_class=HTMLResponse)
async def delete_image(product_id: int, request: Request):
    redirect = _check_admin(request)
    if redirect:
        return redirect
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return HTMLResponse("Товар не найден", status_code=404)

        form = await request.form()
        idx = int(form.get("index", -1))
        images = _get_images(product)

        if 0 <= idx < len(images):
            removed = images.pop(idx)
            fpath = os.path.join(IMAGES_DIR, removed.get("file_id", ""))
            if os.path.exists(fpath):
                os.remove(fpath)

        db.expire(product)
        db.execute(text("UPDATE products SET images = :img WHERE id = :pid"),
                   {"img": json.dumps(images), "pid": product_id})
        db.commit()
        return RedirectResponse(f"{_root(request)}/image-manager/{product_id}", status_code=303)
    finally:
        db.close()

@router_images.post("/{product_id}/move", response_class=HTMLResponse)
async def move_image(product_id: int, request: Request):
    redirect = _check_admin(request)
    if redirect:
        return redirect
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return HTMLResponse("Товар не найден", status_code=404)

        form = await request.form()
        from_idx = int(form.get("from_idx", -1))
        to_idx = int(form.get("to_idx", -1))
        images = _get_images(product)

        if 0 <= from_idx < len(images) and 0 <= to_idx < len(images):
            images[from_idx], images[to_idx] = images[to_idx], images[from_idx]

        db.expire(product)
        db.execute(text("UPDATE products SET images = :img WHERE id = :pid"),
                   {"img": json.dumps(images), "pid": product_id})
        db.commit()
        return RedirectResponse(f"{_root(request)}/image-manager/{product_id}", status_code=303)
    finally:
        db.close()
