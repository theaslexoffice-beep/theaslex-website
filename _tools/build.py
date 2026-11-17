#!/usr/bin/env python3
"""
THE AS LEX — static site builder.

Generates index.html, blog.html, disclaimer.html, 404.html, sitemap.xml, robots.txt
and re-skins every article in blog-posts/ with the shared header/footer.

Single source of truth for the Insights list: _tools/posts.json
Enquiry form wiring (Google Form endpoint + entry ids): _tools/form.json

To publish a new article:
  1. save the article to blog-posts/<slug>.html using .post-hero + .post-body markup
     (copy any existing article as a template)
  2. add an entry to _tools/posts.json (any order — sorted by date)
  3. python3 _tools/build.py
  4. git add . && git commit -m "..." && git push origin main

FIRM RULE: the site shows no individual names, no phone numbers, no email
address, no location and no social links. Contact is through the enquiry form only.
"""
import json, os, re, html, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://theaslex.in"
FORM = json.load(open("_tools/form.json", encoding="utf-8"))
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500'
         '&family=Inter:wght@300;400;500;600&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600&display=swap" rel="stylesheet">')

TAG_LABELS = [
    ("income-tax", "Income Tax"),
    ("international-tax", "International Tax"),
    ("transfer-pricing", "Transfer Pricing"),
    ("gst", "GST"),
    ("securities", "Securities"),
    ("companies", "Companies Act"),
    ("pmla", "PMLA &amp; ED"),
]

ARROW = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M1 8h13M9 3l5 5-5 5"/></svg>'
SEARCH = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="8.5" cy="8.5" r="6"/><path d="M13 13l5 5"/></svg>'

PRACTICE = [
    ("Income Tax",
     "Appeals and representation before the Income Tax Appellate Tribunal for the revenue and for assessees — unexplained credits and cash deposits, reassessment, search and seizure, penalty proceedings and disallowances — and writ remedies before the High Courts where jurisdiction itself is in question.",
     ["ITAT", "s.68 / 69A", "s.147 / 148", "s.270A penalties", "Search &amp; seizure", "Writs"]),
    ("International Tax &amp; Transfer Pricing",
     "Transfer pricing references and DRP proceedings, characterisation and benchmarking disputes, place of effective management, offshore indirect transfers and treaty interpretation.",
     ["Transfer Pricing", "DRP", "POEM", "DTAA", "Indirect transfers"]),
    ("GST",
     "Appeals, investigations and advisory on GST compliance and penalty proceedings, bail in investigation matters, and the resolution of legacy indirect-tax disputes.",
     ["Appeals", "Investigations", "Penalties", "Bail"]),
    ("Securities Law",
     "Representation in SEBI show-cause notice proceedings involving market-manipulation and insider-trading allegations, listing and disclosure compliance, and regulatory strategy.",
     ["SEBI", "Show-cause notices", "PIT / PFUTP", "Disclosure"]),
    ("Companies Act",
     "NCLT proceedings including oppression and mismanagement petitions, schemes of arrangement, mergers and amalgamations, and corporate restructuring.",
     ["NCLT", "Oppression &amp; mismanagement", "Schemes", "Restructuring"]),
    ("PMLA &amp; White Collar",
     "Enforcement Directorate matters — provisional attachment, adjudication and appellate challenges — SFIO investigations, and the defence of economic-offence proceedings.",
     ["ED", "Attachment", "Adjudicating Authority", "SFIO"]),
]
FORUMS = ["ITAT", "NCLT", "SEBI", "Enforcement Directorate", "High Courts", "DRAT"]


# ----------------------------------------------------------------------------
# partials
# ----------------------------------------------------------------------------
def head(root, title, desc, url, extra=""):
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0F1E33">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="The AS Lex">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/logo-512.png">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="{root}style.css">
<script src="{root}site.js" defer></script>{extra}"""


def brand(root):
    return f"""<a href="{root}index.html" class="brand" aria-label="The AS Lex — home">
      <img class="brand-mark" src="{root}assets/logo-mark.svg" alt="" width="44" height="44">
      <span class="brand-word"><span class="brand-name">The AS Lex</span><span class="brand-tag">Tax · Securities · Corporate</span></span>
    </a>"""


def header(root, home=False, active=""):
    h = "" if home else f"{root}index.html"
    def cur(k): return ' aria-current="page"' if k == active else ""
    return f"""<!--site-header-->
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" id="site-header">
  <div class="wrap">
    {brand(root)}
    <button class="nav-toggle" id="nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="main-nav"><span></span><span></span><span></span></button>
    <nav class="main-nav" id="main-nav" aria-label="Primary">
      <a href="{h}#about"{cur('about')}>The Practice</a>
      <a href="{h}#practice"{cur('practice')}>Expertise</a>
      <a href="{h}#approach"{cur('approach')}>Approach</a>
      <a href="{root}blog.html"{cur('insights')}>Insights</a>
      <a href="{h}#contact" class="btn btn-brass">Enquire</a>
    </nav>
  </div>
</header>
<!--/site-header-->"""


def footer(root, home=False):
    h = "" if home else f"{root}index.html"
    prac = "".join(f'<li><a href="{h}#practice">{p[0]}</a></li>' for p in PRACTICE)
    return f"""<!--site-footer-->
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <div>
        {brand(root)}
        <p class="footer-blurb">A specialised practice at the intersection of tax, securities and corporate law, before tribunals, regulators and courts across India.</p>
      </div>
      <div class="footer-col"><h4>Expertise</h4><ul>{prac}</ul></div>
      <div class="footer-col"><h4>The Firm</h4><ul>
        <li><a href="{h}#about">The Practice</a></li>
        <li><a href="{h}#approach">Approach</a></li>
        <li><a href="{root}blog.html">Insights</a></li>
        <li><a href="{h}#contact">Enquiries</a></li></ul></div>
      <div class="footer-col"><h4>Legal</h4><ul>
        <li><a href="{root}disclaimer.html">Disclaimer</a></li>
        <li><a href="{root}disclaimer.html#privacy">Privacy</a></li>
        <li><a href="{root}disclaimer.html#acknowledgement">Acknowledgement</a></li></ul></div>
    </div>
    <div class="footer-legal">
      <p>&copy; <span data-year>2026</span> The AS Lex. All rights reserved.</p>
      <p>In accordance with the rules of the Bar Council of India, this website is not intended to advertise or solicit work. Its content is for information only and is not legal advice. <a href="{root}disclaimer.html">Read the disclaimer</a>.</p>
    </div>
  </div>
</footer>
<!--/site-footer-->"""


def esc(s): return html.escape(s, quote=True)


def fmt_date(d): return datetime.strptime(d, "%Y-%m-%d").strftime("%-d %B %Y")


def card(p, root, with_tags=True):
    tags = f' data-tags="{" ".join(p["tags"])}"' if with_tags else ""
    cat = p["categories"][-1] if p["categories"] else "Insight"
    return f"""<a class="card reveal" href="{root}blog-posts/{p['slug']}.html"{tags}>
  <div class="card-meta"><span class="card-cat">{esc(cat)}</span><span>{fmt_date(p['date'])}</span></div>
  <h3 class="card-title">{p['title']}</h3>
  <p class="card-excerpt">{p['excerpt']}</p>
  <div class="card-foot"><span>{p['read']}</span><span class="go">Read {ARROW}</span></div>
</a>"""


def page(root, title, desc, url, body, active="", home=False, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en-IN" class="no-js">
<head>
{head(root, title, desc, url, extra_head)}
</head>
<body data-root="{root}">
{header(root, home, active)}
<main id="main">
{body}
</main>
{footer(root, home)}
</body>
</html>
"""


# ----------------------------------------------------------------------------
# enquiry form (posts to the firm's Google Form; no address exposed)
# ----------------------------------------------------------------------------
def enquiry_form():
    F = FORM["fields"]
    opts = "".join(f'<option value="{esc(a)}">{esc(a)}</option>' for a in FORM["areas"])
    return f"""<form class="enquiry reveal reveal-d1" id="enquiry-form" action="{FORM['action']}" method="POST" novalidate>
  <div class="enquiry-grid">
    <div class="field"><label for="f-name">Full name <span aria-hidden="true">*</span></label>
      <input id="f-name" name="{F['name']}" type="text" autocomplete="name" required maxlength="120"></div>
    <div class="field"><label for="f-email">Email <span aria-hidden="true">*</span></label>
      <input id="f-email" name="{F['email']}" type="email" autocomplete="email" required maxlength="160"></div>
    <div class="field"><label for="f-phone">Phone <small>(optional)</small></label>
      <input id="f-phone" name="{F['phone']}" type="tel" autocomplete="tel" maxlength="30" inputmode="tel"></div>
    <div class="field"><label for="f-org">Organisation <small>(optional)</small></label>
      <input id="f-org" name="{F['org']}" type="text" autocomplete="organization" maxlength="160"></div>
    <div class="field"><label for="f-area">Area of practice <span aria-hidden="true">*</span></label>
      <select id="f-area" name="{F['area']}" required><option value="" disabled selected>Select an area</option>{opts}</select></div>
    <div class="field"><label for="f-forum">Forum / stage <small>(optional)</small></label>
      <input id="f-forum" name="{F['forum']}" type="text" maxlength="160" placeholder="e.g. ITAT appeal, SCN reply, NCLT petition"></div>
    <div class="field field-full"><label for="f-msg">Brief description of the matter <span aria-hidden="true">*</span></label>
      <textarea id="f-msg" name="{F['message']}" rows="5" required maxlength="4000" placeholder="Please do not include confidential details at this stage."></textarea></div>
    <div class="field field-hp" aria-hidden="true"><label for="f-web">Website</label><input id="f-web" name="hp_website" type="text" tabindex="-1" autocomplete="off"></div>
    <div class="field field-full field-check">
      <input id="f-ack" name="{F['ack']}" type="checkbox" value="Accepted" required>
      <label for="f-ack">I confirm that I am contacting The AS Lex of my own accord, and I understand that submitting this enquiry does not create a lawyer&ndash;client relationship.</label>
    </div>
  </div>
  <div class="enquiry-foot">
    <p class="form-status" role="status" aria-live="polite"></p>
    <button class="btn btn-ink" type="submit">Submit enquiry {ARROW}</button>
  </div>
  <div class="enquiry-done" hidden>
    <span class="eyebrow">Received</span>
    <h3>Thank you. Your enquiry has been received.</h3>
    <p>We will review it and respond at the earliest. Please do not send confidential documents until a professional relationship has been confirmed in writing.</p>
  </div>
</form>"""


# ----------------------------------------------------------------------------
# pages
# ----------------------------------------------------------------------------
def emblem():
    mono = open("assets/logo-mono.svg").read()
    mono = re.sub(r'<svg[^>]*>', '<svg x="110" y="110" width="140" height="140" viewBox="0 0 120 120">', mono, 1)
    return f"""<div class="hero-emblem" aria-hidden="true">
<svg viewBox="0 0 360 360">
  <defs><path id="ring" d="M180,180 m-150,0 a150,150 0 1,1 300,0 a150,150 0 1,1 -300,0"/></defs>
  <circle cx="180" cy="180" r="172" fill="none" stroke="currentColor" stroke-opacity=".35" stroke-width=".8"/>
  <circle cx="180" cy="180" r="128" fill="none" stroke="currentColor" stroke-opacity=".35" stroke-width=".8"/>
  <g class="ring"><text font-family="Inter, sans-serif" font-size="10.5" letter-spacing="5.2" fill="currentColor" fill-opacity=".85">
    <textPath href="#ring" textLength="936" lengthAdjust="spacing">INCOME TAX · INTERNATIONAL TAX · GST · SECURITIES · COMPANIES · PMLA · </textPath></text></g>
  {mono}
</svg></div>"""


def build_index(posts):
    prac = "\n".join(f"""<details class="practice-item reveal"{' open' if i == 0 else ''}>
  <summary><span class="practice-num">{i+1:02d}</span><span class="practice-title">{t}</span><span class="practice-plus" aria-hidden="true"></span></summary>
  <div class="practice-body"><p>{d}</p><ul>{''.join(f'<li>{x}</li>' for x in tags)}</ul></div>
</details>""" for i, (t, d, tags) in enumerate(PRACTICE))
    forums = "".join(f"<li>{f}</li>" for f in FORUMS)
    latest = "\n".join(card(p, "", with_tags=False) for p in posts[:3])
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "LegalService", "name": "The AS Lex",
        "url": SITE, "logo": f"{SITE}/assets/logo-512.png", "areaServed": "IN",
        "description": "A specialised practice at the intersection of tax, securities and corporate law.",
        "knowsAbout": ["Income Tax", "Transfer Pricing", "International Taxation", "GST", "Securities Law", "Companies Act", "PMLA"]}, indent=1)
    body = f"""<section class="hero">
  <div class="hero-body"><div class="wrap hero-grid">
    <div>
      <span class="eyebrow reveal">Tax · Securities · Corporate · PMLA</span>
      <h1 class="display reveal reveal-d1">Where law meets <em>precision.</em></h1>
      <p class="hero-sub reveal reveal-d2">A specialised practice in income tax, international tax, GST, securities regulation, company law and economic offences, appearing before tribunals, regulators and courts across India.</p>
      <div class="hero-cta reveal reveal-d3">
        <a href="#practice" class="btn btn-brass">Our expertise {ARROW}</a>
        <a href="blog.html" class="btn btn-ghost-light">Read insights</a>
      </div>
    </div>
    {emblem()}
  </div></div>
  <div class="hero-forums"><div class="wrap"><span class="hero-forums-label">Forums</span><ul>{forums}</ul></div></div>
</section>

<section class="section" id="about">
  <div class="wrap about-grid">
    <div class="reveal">
      <span class="eyebrow">The Practice</span>
      <h2 class="h2">Technical depth. <em>Strategic</em> advocacy.</h2>
    </div>
    <div class="about-copy reveal reveal-d1">
      <p>A specialised practice at the intersection of tax, securities and corporate law.</p>
      <p>The AS Lex represents clients across India in income tax, GST, securities regulation, corporate governance and economic-offence matters, appearing before tribunals, regulatory authorities and superior courts for both revenue and private interests.</p>
      <p>The practice combines technical precision with strategic advocacy, drawing on accounting, finance and law to handle complex litigation: reassessment proceedings, penalty disputes, SEBI enforcement, NCLT matters and PMLA cases.</p>
    </div>
  </div>
  <div class="wrap">
    <div class="pillars">
      <div class="pillar reveal"><span class="pillar-num">i.</span><h3>Both sides of the dispute</h3><p>Experience on revenue-side and assessee-side matters gives a complete view of how a case will be argued, and how it will be answered.</p></div>
      <div class="pillar reveal reveal-d1"><span class="pillar-num">ii.</span><h3>Numbers, read closely</h3><p>Grounded in accounting and finance. Balance sheets, ledgers and valuation reports are read as evidence, not as annexures.</p></div>
      <div class="pillar reveal reveal-d2"><span class="pillar-num">iii.</span><h3>Drafting as a craft</h3><p>Every submission is built for a busy bench: precise, fully sourced, and structured around the decision it asks for.</p></div>
    </div>
  </div>
</section>

<section class="section section-ivory" id="practice">
  <div class="wrap">
    <div class="section-head">
      <div class="reveal"><span class="eyebrow">Expertise</span><h2 class="h2">Areas of practice</h2></div>
      <p class="lead reveal reveal-d1">Focused on disputes where tax, regulation and corporate law meet, and where the record, the numbers and the drafting decide the outcome.</p>
    </div>
    <div class="practice-list">
{prac}
    </div>
  </div>
</section>

<section class="section section-ink" id="approach">
  <div class="wrap">
    <div class="section-head">
      <div class="reveal"><span class="eyebrow">Approach</span><h2 class="h2">How a matter is run</h2></div>
      <p class="lead reveal reveal-d1">A disciplined method from the first reading of the record to the final hearing.</p>
    </div>
    <div class="approach-grid">
      <div class="approach-step reveal"><div class="num">01</div><h3>Diagnose</h3><p>The record, the timeline and the jurisdiction are examined first: limitation, sanction, authority and service, before the merits.</p></div>
      <div class="approach-step reveal reveal-d1"><div class="num">02</div><h3>Strategise</h3><p>Threshold objections and the merits are sequenced so that the strongest ground leads and every fallback is preserved.</p></div>
      <div class="approach-step reveal reveal-d2"><div class="num">03</div><h3>Draft</h3><p>Grounds, submissions and paper books are written to be read, with every proposition tied to the record and to authority.</p></div>
      <div class="approach-step reveal reveal-d3"><div class="num">04</div><h3>Represent</h3><p>Focused oral advocacy before the bench, with the numbers at hand and an answer ready for the other side.</p></div>
    </div>
  </div>
</section>

<section class="quote-band"><div class="wrap reveal"><blockquote>&ldquo;In tax and regulatory work, the identity of the signatory and the figure in the ledger are rarely formalities.&rdquo;</blockquote><div class="rule"></div></div></section>

<section class="section" id="insights">
  <div class="wrap">
    <div class="section-head">
      <div class="reveal"><span class="eyebrow">Insights</span><h2 class="h2">Recent analysis</h2></div>
      <div class="reveal reveal-d1 section-head-link"><a class="link-arrow" href="blog.html">All insights {ARROW}</a></div>
    </div>
    <div class="cards" id="latest-insights">
{latest}
    </div>
  </div>
</section>

<section class="section section-ivory" id="contact">
  <div class="wrap contact-grid">
    <div class="reveal">
      <span class="eyebrow">Enquiries</span>
      <h2 class="h2">Tell us about your matter</h2>
      <p class="lead">Share a brief outline of the matter, the forum and any relevant dates. Every enquiry is reviewed and answered.</p>
      <ul class="contact-points">
        <li><span>01</span>Submit the enquiry through this form.</li>
        <li><span>02</span>We review it for scope and any conflict of interest.</li>
        <li><span>03</span>We respond to discuss next steps.</li>
      </ul>
      <p class="contact-note">Please do not share confidential or privileged information until a professional relationship has been confirmed in writing. Information submitted is handled as described in our <a href="disclaimer.html#privacy">privacy notice</a>.</p>
    </div>
    {enquiry_form()}
  </div>
</section>"""
    extra = f'\n<script type="application/ld+json">\n{ld}\n</script>'
    return page("", "The AS Lex — Tax, Securities &amp; Corporate Law",
                "The AS Lex is a specialised practice at the intersection of tax, securities and corporate law, before tribunals, regulators and courts across India.",
                SITE + "/", body, home=True, extra_head=extra)


def build_blog(posts):
    f = posts[0]
    used = {t for p in posts for t in p["tags"]}
    chips = '<button class="chip" type="button" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{v}</button>' for k, v in TAG_LABELS if k in used)
    cards = "\n".join(card(p, "") for p in posts)
    body = f"""<section class="page-hero">
  <div class="wrap">
    <div class="crumbs"><a href="index.html">Home</a><span>/</span><span>Insights</span></div>
    <span class="eyebrow">Insights</span>
    <h1 class="display">Analysis &amp; commentary</h1>
    <p class="lead">Practitioner notes on recent rulings and developments in income tax, transfer pricing, securities, company law and PMLA.</p>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap">
    <a class="feature reveal" href="blog-posts/{f['slug']}.html">
      <div class="feature-body">
        <div class="card-meta"><span class="card-cat">Latest · {esc(f['categories'][-1])}</span><span>{fmt_date(f['date'])}</span><span>{f['read']}</span></div>
        <h2>{f['title']}</h2>
        <p>{f['excerpt']}</p>
        <span class="link-arrow">Read the analysis {ARROW}</span>
      </div>
      <div class="feature-art" aria-hidden="true"><div class="big">§<small>Latest analysis</small></div></div>
    </a>

    <div class="toolbar">
      <div class="chips" role="group" aria-label="Filter by practice area">{chips}</div>
      <label class="search">{SEARCH}<span class="sr-only">Search insights</span><input id="insight-search" type="search" placeholder="Search insights" autocomplete="off"></label>
    </div>
    <div class="cards" id="insight-list">
{cards}
    </div>
    <p class="empty-state" id="insight-empty">No insights match your search.</p>
  </div>
</section>"""
    return page("", "Insights — The AS Lex",
                "Practitioner analysis from The AS Lex on income tax, transfer pricing, international tax, securities, company law and PMLA.",
                SITE + "/blog.html", body, active="insights")


def build_disclaimer():
    body = """<section class="page-hero">
  <div class="wrap">
    <div class="crumbs"><a href="index.html">Home</a><span>/</span><span>Disclaimer</span></div>
    <span class="eyebrow">Legal</span>
    <h1 class="display">Disclaimer &amp; Privacy</h1>
  </div>
</section>
<article class="legal">
  <h2 id="acknowledgement">Acknowledgement</h2>
  <p>The rules of the Bar Council of India do not permit advocates to solicit work or advertise in any manner. By accessing this website, the user acknowledges that they are seeking information about The AS Lex of their own accord, for their own information and use, and that there has been no advertisement, personal communication, solicitation, invitation or inducement of any sort whatsoever from The AS Lex or any of its members to solicit any work through this website.</p>

  <h2 id="disclaimer">Disclaimer</h2>
  <p>The material on this website, including the articles published under &ldquo;Insights&rdquo;, is provided for general informational purposes only. It does not constitute legal, tax or other professional advice and must not be relied upon as such. Every matter turns on its own facts; specific advice should be obtained before acting on any information on this website.</p>
  <p>While reasonable care is taken in preparing the content, The AS Lex does not warrant that it is accurate, complete or current, and disclaims all liability to any person for any loss or damage caused by errors or omissions, or by any action taken or not taken on the basis of the content, whether such errors or omissions result from negligence, accident or any other cause.</p>
  <p>Summaries of judgments and orders are prepared from the text available at the time of writing and should be read against the certified copy. The law may have changed since publication.</p>
  <p>Use of this website, including the submission of an enquiry, does not create a lawyer&ndash;client or any other professional relationship. Links to third-party websites are provided for convenience only; The AS Lex is not responsible for, and does not endorse, their content.</p>

  <h2 id="privacy">Privacy</h2>
  <p>This website does not use advertising or tracking cookies and does not run analytics. A single entry is stored in your browser&rsquo;s local storage to remember that you have accepted the acknowledgement; it is not transmitted to us and expires after 30 days.</p>
  <p>Enquiries submitted through the enquiry form are transmitted to, and stored in, the firm&rsquo;s own Google Workspace account (Google Forms and Google Sheets). The information is used only to review and respond to your enquiry, including a conflict check, and is not shared with third parties or used for marketing.</p>
  <p>Fonts are served by Google Fonts, which may receive your IP address when a page loads.</p>
  <ul>
    <li>Please do not submit confidential or privileged information until a professional relationship has been confirmed in writing.</li>
    <li>You may ask for an enquiry you submitted to be deleted by sending a further enquiry through the same form with that request.</li>
    <li>To withdraw your acknowledgement, clear this site&rsquo;s data in your browser; the acknowledgement will be shown again on your next visit.</li>
  </ul>

  <h2 id="ip">Intellectual property</h2>
  <p>All content on this website is the property of The AS Lex unless otherwise stated. Content may be quoted with attribution for non-commercial purposes; any other reproduction requires prior written permission.</p>
</article>"""
    return page("", "Disclaimer &amp; Privacy — The AS Lex", "Bar Council of India acknowledgement, disclaimer and privacy notice for theaslex.in.",
                SITE + "/disclaimer.html", body)


def build_404():
    body = f"""<section class="page-hero page-hero-tall">
  <div class="wrap">
    <span class="eyebrow">Error 404</span>
    <h1 class="display">This page could not be found.</h1>
    <p class="lead">The page may have moved, or the link may be out of date.</p>
    <div class="hero-cta"><a href="/" class="btn btn-brass">Return home {ARROW}</a><a href="/blog.html" class="btn btn-ghost-light">Browse insights</a></div>
  </div>
</section>"""
    # 404 is served from arbitrary paths on GitHub Pages → absolute root
    return page("/", "Page not found — The AS Lex", "Page not found.", SITE + "/404.html", body)


# ----------------------------------------------------------------------------
# articles: swap legacy chrome for the shared header/footer (idempotent)
# ----------------------------------------------------------------------------
def reskin_post(path, meta):
    s = open(path, encoding="utf-8").read()
    R = "../"
    # <head>: remove what we own, then inject the shared block once
    s = re.sub(r'\s*<!--site-head-->.*?<!--/site-head-->', '', s, flags=re.S)
    s = re.sub(r'\s*<link rel="icon" href="data:[^"]*"\s*/?>', '', s)          # legacy data-URI favicons
    s = re.sub(r"<rect width='100'[^\n]*?</svg>\" />", '', s)                 # debris of an earlier strip
    for pat in (r'<link rel="icon"[^>]*>', r'<link rel="apple-touch-icon"[^>]*>', r'<link rel="preconnect"[^>]*>',
                r'<link href="https://fonts\.googleapis\.com[^>]*>', r'<link rel="stylesheet" href="\.\./style\.css"\s*/?>',
                r'<meta name="theme-color"[^>]*>', r'<link rel="canonical"[^>]*>', r'<meta property="og:[^>]*>',
                r'<meta name="twitter:[^>]*>'):
        s = re.sub(r'\s*' + pat, '', s)
    s = re.sub(r'<style>.*?</style>\s*', '', s, flags=re.S)              # legacy per-post themes
    plain_title = html.unescape(re.sub('<[^>]+>', '', meta["title"]))
    url = f"{SITE}/blog-posts/{meta['slug']}.html"
    inject = f"""
<!--site-head-->
<meta name="theme-color" content="#0F1E33">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The AS Lex">
<meta property="og:title" content="{esc(plain_title)}">
<meta property="og:description" content="{esc(html.unescape(re.sub('<[^>]+>', '', meta['excerpt'])))}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/logo-512.png">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{R}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{R}assets/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="{R}style.css">
<!--/site-head-->"""
    s = s.replace("</head>", inject + "\n</head>", 1)
    s = re.sub(r'<html[^>]*>', '<html lang="en-IN" class="no-js">', s, 1)
    s = re.sub(r'<body[^>]*>', f'<body data-root="{R}">', s, 1)

    # header
    hdr = header(R, active="insights") + '\n<div class="read-progress" aria-hidden="true"></div>\n<main id="main">'
    if "<!--site-header-->" in s:
        s = re.sub(r'<!--site-header-->.*?<!--/site-header-->\s*<div class="read-progress"[^>]*></div>\s*<main id="main">',
                   lambda m: hdr, s, count=1, flags=re.S)
    else:
        s = re.sub(r'(<!--\s*(NAV|Navigation)[^>]*-->\s*)?<nav\b.*?</nav>', lambda m: hdr, s, count=1, flags=re.S)

    # footer + scripts
    end = f"""</main>
<section class="post-end"><div class="wrap"><p>More analysis from The AS Lex</p><a href="{R}blog.html" class="btn btn-ink">All insights {ARROW}</a></div></section>
{footer(R)}
<script src="{R}site.js" defer></script>"""
    if "<!--site-footer-->" in s:
        s = re.sub(r'</main>\s*<section class="post-end">.*?<!--/site-footer-->\s*<script src="\.\./site\.js" defer></script>',
                   lambda m: end, s, count=1, flags=re.S)
    else:
        s = re.sub(r'<div style="text-align: center; padding: 3rem 5% 6rem;[^"]*">\s*<a href="\.\./blog\.html" class="btn-outline">.*?</a>\s*</div>\s*', '', s, flags=re.S)
        s = re.sub(r'(<!--\s*FOOTER\s*-->\s*)?<footer\b.*?</footer>\s*', '', s, count=1, flags=re.S)
        s = re.sub(r'(<!--[^>]*Script[^>]*-->\s*)?<script(?![^>]*application/ld\+json)[^>]*>.*?</script>\s*', '', s, flags=re.S)
        s = s.replace("</body>", end + "\n</body>", 1)

    # firm rule: no email address on the site — route every mailto to the enquiry form
    s = re.sub(r'<a href="mailto:[^"]*"[^>]*>[^<]*</a>', f'<a href="{R}index.html#contact">our enquiry form</a>', s)
    open(path, "w", encoding="utf-8").write(s)


def sitemap(posts):
    urls = [(SITE + "/", posts[0]["date"]), (SITE + "/blog.html", posts[0]["date"]), (SITE + "/disclaimer.html", None)]
    urls += [(f"{SITE}/blog-posts/{p['slug']}.html", p["date"]) for p in posts]
    body = "".join(f"  <url><loc>{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>\n" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n'


def audit():
    """Fail the build if anything that must never be public slipped in."""
    bad = []
    for dp, _, fs in os.walk("."):
        if dp.startswith(("./.git", "./_tools", "./.vercel")): continue
        for fn in fs:
            if not fn.endswith((".html", ".js", ".xml")): continue
            t = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            for label, rx in (("email", r"mailto:|[\w.+-]+@(?:gmail|theaslex|yahoo|outlook)\.\w+"),
                              ("phone", r"tel:|\+91[\s-]?\d|(?<![\d.])[6-9]\d{4}[\s-]?\d{5}(?![\d.])"),
                              ("linkedin", r"linkedin\.com")):
                if re.search(rx, t): bad.append(f"{dp}/{fn}: {label}")
    return bad


def main():
    posts = json.load(open("_tools/posts.json", encoding="utf-8"))
    posts.sort(key=lambda p: p["date"], reverse=True)
    missing = [p["slug"] for p in posts if not os.path.exists(f"blog-posts/{p['slug']}.html")]
    if missing: sys.exit(f"missing article files: {missing}")
    open("index.html", "w").write(build_index(posts))
    open("blog.html", "w").write(build_blog(posts))
    open("disclaimer.html", "w").write(build_disclaimer())
    open("404.html", "w").write(build_404())
    open("sitemap.xml", "w").write(sitemap(posts))
    open("robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    for p in posts: reskin_post(f"blog-posts/{p['slug']}.html", p)
    print(f"built: index, blog ({len(posts)} posts), disclaimer, 404, sitemap; re-skinned {len(posts)} articles")
    bad = audit()
    if bad:
        print("PRIVACY AUDIT FAILED:\n  " + "\n  ".join(bad)); sys.exit(1)
    print("privacy audit: clean (no email / phone / LinkedIn on any public page)")


if __name__ == "__main__":
    main()
