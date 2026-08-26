# -*- coding: utf-8 -*-
import json
import logging
import re
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

def execute_website_inspect_page(env, args):
    """
    Inspect a website page's QWeb architecture, SEO metadata, and publication status.
    """
    url = args.get("url")
    page_id = args.get("page_id")
    
    page = None
    if "website.page" in env:
        if page_id:
            page = env["website.page"].browse(int(page_id))
        elif url:
            page = env["website.page"].search([("url", "=", url)], limit=1)
            
    if page and page.exists():
        view = page.view_id
        arch_str = view.arch_base or view.arch or ""
        snippets = _extract_snippets_summary(arch_str)
        return {
            "page_id": page.id,
            "name": page.name,
            "url": page.url,
            "is_published": getattr(page, 'is_published', True),
            "meta_title": getattr(page, 'website_meta_title', '') or page.name,
            "meta_description": getattr(page, 'website_meta_description', '') or '',
            "meta_keywords": getattr(page, 'website_meta_keywords', '') or '',
            "snippets_found": snippets,
            "arch_length": len(arch_str),
        }
    
    # Fallback to ir.ui.view if website.page not found or not present
    if page_id or url:
        view_domain = [('key', '=', url)] if url else [('id', '=', int(page_id))]
        view = env['ir.ui.view'].search(view_domain, limit=1)
        if view:
            arch_str = view.arch_base or view.arch or ""
            return {
                "view_id": view.id,
                "name": view.name,
                "key": view.key,
                "snippets_found": _extract_snippets_summary(arch_str),
                "arch_length": len(arch_str),
            }
            
    return {
        "status": "not_found",
        "message": f"Website page or view not found for url='{url}' / page_id='{page_id}'."
    }

def execute_website_update_seo(env, args):
    """
    Update SEO metadata (title, description, keywords) for a website page.
    """
    page_id = args.get("page_id")
    url = args.get("url")
    meta_title = args.get("meta_title")
    meta_description = args.get("meta_description")
    keywords = args.get("keywords")
    
    if isinstance(keywords, list):
        keywords = ", ".join(str(k) for k in keywords)

    page = None
    if "website.page" in env:
        if page_id:
            page = env["website.page"].browse(int(page_id))
        elif url:
            page = env["website.page"].search([("url", "=", url)], limit=1)

    if not page or not page.exists():
        return {"error": f"Target website page not found for id={page_id} / url={url}"}

    vals = {}
    if meta_title:
        vals["website_meta_title"] = meta_title
    if meta_description:
        vals["website_meta_description"] = meta_description
    if keywords:
        vals["website_meta_keywords"] = keywords

    page.write(vals)
    return {
        "status": "success",
        "page_id": page.id,
        "url": page.url,
        "updated_fields": list(vals.keys()),
        "message": f"SEO metadata updated successfully for page '{page.name}' ({page.url})."
    }

def execute_website_generate_snippet(env, args):
    """
    Generate responsive Bootstrap 5 / QWeb HTML snippet blocks for Odoo Website.
    Supported types: hero, features, testimonials, pricing, faqs, cta.
    """
    snippet_type = (args.get("snippet_type") or "features").lower()
    title = args.get("title") or "Enhanced Section"
    subtitle = args.get("subtitle") or ""
    items = args.get("items") or []
    
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = [{"title": items, "description": ""}]

    if snippet_type == "hero":
        cta_text = args.get("cta_text") or "Get Started Now"
        cta_url = args.get("cta_url") or "/contactus"
        html = f"""<section class="s_banner pt96 pb96 bg-primary-light text-center">
    <div class="container">
        <h1 class="display-4 fw-bold mb-3">{title}</h1>
        <p class="lead text-muted mb-4">{subtitle}</p>
        <a href="{cta_url}" class="btn btn-primary btn-lg shadow-sm px-4">{cta_text}</a>
    </div>
</section>"""

    elif snippet_type == "features":
        cards_html = []
        for item in items:
            item_title = item.get("title") if isinstance(item, dict) else str(item)
            item_desc = item.get("description") if isinstance(item, dict) else ""
            item_icon = item.get("icon", "fa-check-circle") if isinstance(item, dict) else "fa-check-circle"
            cards_html.append(f"""        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card h-100 border-0 shadow-sm p-4 text-center">
                <div class="mb-3 text-primary"><i class="fa {item_icon} fa-3x"></i></div>
                <h4 class="card-title fw-bold">{item_title}</h4>
                <p class="card-text text-muted">{item_desc}</p>
            </div>
        </div>""")
        cards_str = "\n".join(cards_html)
        html = f"""<section class="s_three_columns pt64 pb64 bg-light">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="fw-bold">{title}</h2>
            <p class="text-muted">{subtitle}</p>
        </div>
        <div class="row">
{cards_str}
        </div>
    </div>
</section>"""

    elif snippet_type == "faqs":
        acc_items = []
        for idx, item in enumerate(items):
            q = item.get("question") or item.get("title") if isinstance(item, dict) else str(item)
            a = item.get("answer") or item.get("description") if isinstance(item, dict) else ""
            item_id = f"faq_item_{idx+1}"
            acc_items.append(f"""        <div class="accordion-item border-0 mb-3 shadow-sm rounded">
            <h2 class="accordion-header" id="heading_{item_id}">
                <button class="accordion-button collapsed fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_{item_id}">
                    {q}
                </button>
            </h2>
            <div id="collapse_{item_id}" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                <div class="accordion-body text-muted">{a}</div>
            </div>
        </div>""")
        acc_str = "\n".join(acc_items)
        html = f"""<section class="s_faq pt64 pb64 bg-white">
    <div class="container" style="max-width: 800px;">
        <div class="text-center mb-5">
            <h2 class="fw-bold">{title}</h2>
            <p class="text-muted">{subtitle}</p>
        </div>
        <div class="accordion" id="faqAccordion">
{acc_str}
        </div>
    </div>
</section>"""

    elif snippet_type == "cta":
        cta_text = args.get("cta_text") or "Contact Us Today"
        cta_url = args.get("cta_url") or "/contactus"
        html = f"""<section class="s_call_to_action pt64 pb64 bg-dark text-white text-center">
    <div class="container">
        <h2 class="fw-bold mb-3">{title}</h2>
        <p class="lead mb-4 text-light opacity-75">{subtitle}</p>
        <a href="{cta_url}" class="btn btn-warning btn-lg fw-bold px-5">{cta_text}</a>
    </div>
</section>"""

    else:
        # Generic block
        html = f"""<section class="s_text_block pt48 pb48">
    <div class="container">
        <h2 class="fw-bold mb-2">{title}</h2>
        <p class="lead text-muted">{subtitle}</p>
    </div>
</section>"""

    return {
        "status": "success",
        "snippet_type": snippet_type,
        "title": title,
        "generated_html": html,
        "character_count": len(html),
    }

def execute_website_mutate_page_arch(env, args):
    """
    Safely append or inject a QWeb snippet block into a website page's view arch.
    """
    page_id = args.get("page_id")
    url = args.get("url")
    snippet_html = args.get("snippet_html")
    action = args.get("action", "append") # append, prepend
    
    if not snippet_html:
        return {"error": "No snippet_html provided for mutation."}

    page = None
    if "website.page" in env:
        if page_id:
            page = env["website.page"].browse(int(page_id))
        elif url:
            page = env["website.page"].search([("url", "=", url)], limit=1)

    if not page or not page.exists():
        return {"error": f"Target page not found for page_id={page_id} / url={url}"}

    view = page.view_id
    if not view:
        return {"error": "Page has no associated ir.ui.view."}

    arch = view.arch_base or view.arch or ""
    
    # Safe insertion: append inside the main container or root element
    if "</t>" in arch:
        # Insert before closing </t>
        insert_idx = arch.rfind("</t>")
        new_arch = arch[:insert_idx] + "\n" + snippet_html + "\n" + arch[insert_idx:]
    elif "</div>" in arch:
        insert_idx = arch.rfind("</div>")
        new_arch = arch[:insert_idx] + "\n" + snippet_html + "\n" + arch[insert_idx:]
    else:
        new_arch = arch + "\n" + snippet_html

    # Validate XML syntax before writing
    try:
        from lxml import etree
        etree.fromstring(f"<root>{new_arch}</root>")
    except Exception as e:
        return {"error": f"QWeb arch syntax validation failed: {str(e)}"}

    view.write({"arch_base": new_arch})
    return {
        "status": "success",
        "page_id": page.id,
        "url": page.url,
        "action": action,
        "message": f"Successfully injected QWeb snippet into page '{page.name}' ({page.url})."
    }

def execute_ecommerce_enrich_product_page(env, args):
    """
    Enrich an e-commerce product template with high-converting sections (highlights, specs, FAQs).
    """
    product_tmpl_id = args.get("product_tmpl_id")
    selling_points = args.get("selling_points") or []
    faq_items = args.get("faq_items") or []
    specs = args.get("specs") or {}
    
    product = env["product.template"].browse(int(product_tmpl_id))
    if not product.exists():
        return {"error": f"Product template ID {product_tmpl_id} not found."}

    # Build rich HTML showcase
    parts = []
    
    # 1. Key Value Proposition Highlights
    if selling_points:
        points_html = "".join([f"<li class='mb-2'><i class='fa fa-check-circle text-success me-2'></i>{p}</li>" for p in selling_points])
        parts.append(f"""<div class="oe_product_enrich_highlights my-4 p-4 bg-light rounded shadow-sm">
    <h4 class="fw-bold mb-3"><i class="fa fa-star text-warning me-2"></i>Key Product Highlights</h4>
    <ul class="list-unstyled mb-0">{points_html}</ul>
</div>""")

    # 2. Technical Specifications Table
    if specs and isinstance(specs, dict):
        rows = "".join([f"<tr><th class='w-25 text-muted'>{k}</th><td>{v}</td></tr>" for k, v in specs.items()])
        parts.append(f"""<div class="oe_product_enrich_specs my-4">
    <h4 class="fw-bold mb-3"><i class="fa fa-sliders text-primary me-2"></i>Technical Specifications</h4>
    <table class="table table-bordered table-striped">{rows}</table>
</div>""")

    # 3. Product FAQs Accordion
    if faq_items:
        faq_blocks = []
        for i, item in enumerate(faq_items):
            q = item.get("question") if isinstance(item, dict) else str(item)
            a = item.get("answer") if isinstance(item, dict) else ""
            faq_blocks.append(f"""<div class="accordion-item">
    <h2 class="accordion-header"><button class="accordion-button collapsed fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#prod_faq_{i}">{q}</button></h2>
    <div id="prod_faq_{i}" class="accordion-collapse collapse"><div class="accordion-body text-muted">{a}</div></div>
</div>""")
        faq_str = "".join(faq_blocks)
        parts.append(f"""<div class="oe_product_enrich_faqs my-4">
    <h4 class="fw-bold mb-3"><i class="fa fa-question-circle text-info me-2"></i>Frequently Asked Questions</h4>
    <div class="accordion" id="prodFaqAcc">{faq_str}</div>
</div>""")

    full_html = "\n".join(parts)
    
    # Write to description_ecommerce (or fallback to description_sale)
    vals = {}
    if "description_ecommerce" in product._fields:
        vals["description_ecommerce"] = full_html
    elif "description_sale" in product._fields:
        vals["description_sale"] = full_html
        
    if vals:
        product.write(vals)

    return {
        "status": "success",
        "product_id": product.id,
        "product_name": product.name,
        "updated_field": list(vals.keys())[0] if vals else None,
        "message": f"Enriched e-commerce showcase successfully for '{product.name}'."
    }

def _extract_snippets_summary(arch):
    """Utility helper to scan QWeb arch string and identify snippet components."""
    if not arch:
        return []
    snippet_classes = re.findall(r'class="[^"]*(s_[a-zA-Z0-9_]+)[^"]*"', arch)
    return list(set(snippet_classes))
