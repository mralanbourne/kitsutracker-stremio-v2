import datetime
import logging
import json
from quart import Response, flash, jsonify, redirect, request, url_for
import httpx

async def handle_auth_error(err: httpx.HTTPStatusError):
    if not err.response:
        await flash("No valid response from Kitsu. Service might be down.", "danger")
        return redirect(url_for("ui.index"))
    try:
        response = err.response.json()
        await flash(response.get("message", "Unknown error"), "danger")
    except ValueError:
        await flash("Invalid response from Kitsu.", "danger")
    return redirect(url_for("ui.index"))

async def respond_with(
    data: dict,
    private: bool = False,
    cache_max_age: int = 0,
    stale_revalidate: int = 0,
    stale_error: int = 0,
    stremio_response: bool = False,
) -> Response:
    if stremio_response:
        data["cacheMaxAge"] = cache_max_age
        data["staleRevalidate"] = stale_revalidate

    resp = jsonify(data)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "*"

    if cache_max_age > 0:
        cc_parts = ["private" if private else "public"]
        cc_parts.append(f"max-age={cache_max_age}")
        
        if not private:
            cc_parts.append(f"s-maxage={cache_max_age}")
        if stale_revalidate > 0:
            cc_parts.append(f"stale-while-revalidate={stale_revalidate}")

        resp.headers["Cache-Control"] = ", ".join(cc_parts)
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_max_age)
        resp.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        await resp.add_etag(True)
        await resp.make_conditional(request)

    return resp
