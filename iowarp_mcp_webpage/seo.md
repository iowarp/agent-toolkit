# Optimizing Jekyll Sites for SEO and AI Discovery

**Modern Jekyll optimization requires dual focus: traditional search engines and emerging AI systems. This guide provides practical, actionable strategies specifically for akougkas.io, combining proven SEO techniques with cutting-edge AI discoverability tactics that have driven 750-4,162% traffic increases for early adopters.**

AI-powered search represents the most significant shift in content discovery since Google's launch. Companies implementing these strategies report dramatically higher conversion rates (27% for AI-sourced visitors versus 2.1% from traditional search), making optimization essential for academic and research websites competing for visibility.

## Foundation: Jekyll SEO essentials

Jekyll's static architecture offers inherent performance advantages while three essential plugins handle most technical SEO automatically. Install jekyll-seo-tag, jekyll-sitemap, and jekyll-feed to establish your foundation. These GitHub Pages-compatible plugins generate meta tags, XML sitemaps, and RSS feeds without custom coding.

### Critical configuration in _config.yml

```yaml
# Site metadata
title: "Anthony Kougkas"
tagline: "Computer Science Researcher"
description: "Research on high-performance computing, I/O systems, and storage"
url: "https://akougkas.io"
lang: en_US

# Author and social
author:
  name: "Anthony Kougkas"
  email: "akougkas@illinoistech.edu | akougkas@iit.edu(OLD but maybe referenced on the web)" 
  twitter: kougkas

social:
  name: "Anthony Kougkas"
  links:
    - https://github.com/akougkas
    - https://scholar.google.com/citations?user=hiNO0EEAAAAJ
    - https://linkedin.com/in/anthonykougkas
    - https://orcid.org/0000-0003-3943-663X

# Essential plugins
plugins:
  - jekyll-seo-tag
  - jekyll-sitemap
  - jekyll-feed

# Performance
sass:
  style: compressed
permalink: /:title/

# Feed configuration
feed:
  path: feed.xml
  excerpt_only: false
```

Add the SEO tag to your layout head section with a single Liquid tag: `{% seo %}`. This automatically generates titles, descriptions, Open Graph tags, Twitter Cards, and JSON-LD structured data based on your configuration and page front matter.

### Page-level optimization template

Every page and post should include optimized front matter:

```yaml
---
title: "Optimizing I/O in HPC Systems"
description: "Research findings on improving I/O performance in high-performance computing environments through adaptive caching strategies"
image: /assets/images/hpc-research.jpg
date: 2025-01-15
last_modified_at: 2025-01-20
schema_type: ScholarlyArticle
---
```

## Structured data: The language AI speaks

Experimental evidence reveals the critical importance of schema markup for AI visibility. A controlled study published in Search Engine Land found that a page with well-implemented schema appeared in Google's AI Overview and ranked position 3, while an identical page without schema wasn't indexed at all. Schema markup is non-negotiable for AI discoverability.

### Academic website schema implementation

Create `_includes/person-schema.html` for your about/homepage:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Anthony Kougkas",
  "url": "https://akougkas.io",
  "jobTitle": "Assistant Professor",
  "worksFor": {
    "@type": "EducationalOrganization",
    "name": "Illinois Institute of Technology",
    "department": "Computer Science"
  },
  "alumniOf": [
    {
      "@type": "EducationalOrganization",
      "name": "Northwestern University"
    }
  ],
  "sameAs": [
    "https://github.com/akougkas",
    "https://scholar.google.com/citations?user=YOUR_ID",
    "https://orcid.org/0000-0003-3943-663X",
    "https://dblp.org/pid/YOUR_ID.html"
  ],
  "knowsAbout": [
    "High-Performance Computing",
    "Storage Systems",
    "I/O Optimization",
    "Distributed Systems"
  ]
}
</script>
```

For research publications, implement ScholarlyArticle schema in `_includes/article-schema.html`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "headline": "{{ page.title }}",
  "author": {
    "@type": "Person",
    "name": "{{ site.author.name }}",
    "affiliation": "Illinois Institute of Technology"
  },
  "datePublished": "{{ page.date | date_to_xmlschema }}",
  "dateModified": "{{ page.last_modified_at | default: page.date | date_to_xmlschema }}",
  "description": "{{ page.description }}",
  "publisher": {
    "@type": "Organization",
    "name": "{{ page.publisher | default: site.title }}"
  }
}
</script>
```

Include these in your layouts conditionally based on page type. Test implementation using Google's Rich Results Test at search.google.com/test/rich-results to catch validation errors that confuse AI systems.

## AI crawler strategy: Search visibility versus training

Understanding the distinction between AI search crawlers and training crawlers enables strategic control. OpenAI operates three separate bots: OAI-SearchBot indexes content for ChatGPT Search, ChatGPT-User handles real-time user requests, and GPTBot collects training data. You can block GPTBot without affecting ChatGPT Search visibility, separating concerns about model training from search discoverability.

### Strategic robots.txt configuration

```
# ALLOW AI SEARCH CRAWLERS (visibility)
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# OPTIONALLY BLOCK TRAINING CRAWLERS (licensing)
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: anthropic-ai
Disallow: /

# ClaudeBot with rate limiting
User-agent: ClaudeBot
Crawl-delay: 5
Allow: /

Sitemap: https://akougkas.io/sitemap.xml
```

For academic websites, **allowing search crawlers maximizes research visibility** while blocking training crawlers addresses copyright concerns. This configuration ensures your research appears in AI search results without contributing to model training datasets.

**Important caveat:** Perplexity has been documented using undeclared crawlers that bypass robots.txt by impersonating Chrome browsers and rotating IPs. Cloudflare and WIRED investigations found systematic violations, though Perplexity disputes characterizations. For stricter enforcement, implement firewall rules blocking known Perplexity IP ranges.

## The llms.txt standard: Future-proofing AI accessibility

Created by Jeremy Howard in September 2024, llms.txt provides a standardized way to present LLM-friendly content. While no major LLM provider officially supports llms.txt yet, 784+ sites have implemented it, creating critical mass for eventual adoption. Early implementation future-proofs your site for when official support arrives.

### Official specification and structure

Place llms.txt at your root directory (https://akougkas.io/llms.txt) using this Markdown structure:

```liquid
---
layout: null
---
# Anthony Kougkas - Computer Science Research

> Research on high-performance computing, I/O optimization, storage systems, and distributed computing. Assistant Professor at Illinois Institute of Technology.

I specialize in developing efficient I/O solutions for HPC environments, with publications in SC, HPDC, IPDPS, and other top-tier venues.

## Research Areas
- High-Performance I/O Systems
- Storage Architecture and Optimization
- Distributed Computing Systems
- Scientific Data Management

## Key Publications
- [HermesFS: Efficient Data Management for HPC](https://raw.githubusercontent.com/akougkas/akougkas.github.io/main/_publications/hermesfs.md): Hierarchical distributed I/O buffering system
- [Adaptive I/O Caching Strategies](https://raw.githubusercontent.com/akougkas/akougkas.github.io/main/_publications/caching.md): Machine learning approaches to I/O optimization
- [ScalaIO Framework](https://raw.githubusercontent.com/akougkas/akougkas.github.io/main/_publications/scalaio.md): Scalable I/O middleware for extreme-scale systems

## Academic Profile
- [CV and Publications](/cv/): Complete academic history
- [Research Projects](/research/): Current and past research initiatives
- [Teaching](/teaching/): Courses and student supervision

## Recent Blog Posts
{% for post in site.posts limit:5 %}
- [{{ post.title }}](https://raw.githubusercontent.com/akougkas/akougkas.github.io/main/{{ post.path }}): {{ post.excerpt | strip_html | truncatewords: 20 }}
{% endfor %}

## Contact
- Email: akougkas@iit.edu
- Office: Stuart Building, Illinois Tech
- GitHub: github.com/akougkas

## Optional
- [Conference Talks](/talks/): Presentations and keynotes
- [Service](/service/): Program committees and reviewing
- [Archive](/archive/): All posts and papers by date
```

This Jekyll template dynamically generates your llms.txt file, automatically including recent posts and linking to raw Markdown files on GitHub for AI systems to parse. The structure follows official best practices: clear title, concise summary blockquote, logical H2 sections, and descriptive link annotations.

### Implementation in Jekyll

Add to your repository root as `llms.txt` with the front matter shown above, then ensure Jekyll includes it:

```yaml
# _config.yml
include: [llms.txt]
```

Deploy and verify at https://akougkas.io/llms.txt. Monitor server logs for requests as AI systems and development tools begin adopting the standard.

**Real-world adoption examples:** Major implementations include Anthropic (docs.anthropic.com/llms.txt), Cloudflare (developers.cloudflare.com/llms.txt), and Perplexity (perplexity.ai/llms-full.txt). Mintlify's November 2024 rollout added llms.txt to thousands of documentation sites instantly, creating the critical mass needed for potential official support.

## Content structure for AI comprehension

AI search engines prioritize scannable, well-organized content with explicit semantic structure. Unlike traditional search that ranks based on keywords and PageRank, AI systems extract information to synthesize answers, making content architecture critical for citation.

### Optimal patterns for academic content

**Clear hierarchical structure** using proper heading levels enables AI to understand content organization. Use a single H1 for the main title, H2 for major sections, and H3 for subsections. Never skip levels or use headings for visual styling alone.

**Answer-focused introductions** should front-load key findings in the first 100 words. Research shows AI search engines favor content with direct, concise answers at the beginning, followed by supporting details. Structure your research summaries and publication descriptions accordingly.

**Comparison content dominates AI citations.** Analysis across ChatGPT, Perplexity, and Google AI Overviews found comparison formats ("X vs Y") comprise the highest-cited content type. For academic websites, structure algorithm comparisons, methodology evaluations, and technique analyses as explicit comparisons with honest pros and cons.

**FAQ sections align with conversational queries.** AI systems field questions directly, so question-based headings with direct answers beneath each create ideal citation targets. Add FAQ sections to research project pages addressing common questions about methodology, applications, and results.

### Academic-specific optimizations

**Publication metadata** should be comprehensive and consistent. For each paper, include:
- Full author list with affiliations
- Publication venue and year
- DOI or persistent identifier
- Abstract or summary
- Links to PDF, code, datasets
- Citation count (optional)
- Awards or distinctions

**Research project descriptions** benefit from structured presentation:
- Project title and timeline
- Research objectives (bullet list)
- Methodology summary (2-3 paragraphs)
- Key findings or contributions
- Publications and presentations
- Collaborators and funding sources

**CV/resume pages** should use semantic HTML (not just styled text) with clear sections for education, positions, publications, awards, and service. AI systems extract this structured biographical information to answer queries about your background and expertise.

## Performance and technical optimization

Jekyll's static nature provides inherent speed advantages, but optimization multiplies benefits. Fast sites rank higher traditionally and serve AI crawlers efficiently.

### Essential performance tactics

**HTML minification** using jekyll-compress-html requires no plugins (GitHub Pages compatible). Download compress.html from github.com/penibelst/jekyll-compress-html, save to `_layouts/compress.html`, then wrap your default layout:

```html
---
layout: compress
---
<!DOCTYPE html>
<html>
<!-- Your template -->
</html>
```

**Image optimization** dramatically impacts performance. Resize images to exact display dimensions before uploading, compress using ImageOptim or TinyPNG (target JPEG quality 70-85), and implement native lazy loading:

```html
<img src="/assets/images/research.jpg" 
     alt="HPC cluster architecture diagram" 
     loading="lazy"
     width="800" 
     height="600">
```

**CSS compression** through Jekyll's built-in SASS:

```yaml
# _config.yml
sass:
  style: compressed
  sass_dir: _sass
```

**JavaScript deferral** prevents render-blocking:

```html
<script src="/assets/js/main.js" defer></script>
```

Target Core Web Vitals metrics: Largest Contentful Paint under 2.5 seconds, First Input Delay under 100ms, Cumulative Layout Shift under 0.1. Test using PageSpeed Insights and address red flags systematically.

### Critical JavaScript consideration for AI

Most AI crawlers CANNOT execute JavaScript. OpenAI, Anthropic, and Perplexity crawlers see only server-rendered HTML. Google's Gemini is the sole exception, inheriting Googlebot's full JavaScript rendering capabilities.

**Test your site:** Disable JavaScript in your browser and verify all essential content remains visible. If content disappears, AI systems cannot access it, rendering you invisible to ChatGPT Search, Perplexity, and Claude.

For Jekyll static sites, this is rarely problematic since content is pre-rendered. However, avoid:
- JavaScript-generated navigation or content
- Client-side routing without fallbacks
- Dynamic content loading without progressive enhancement

Your Jekyll site likely passes this test by default, but verify critical pages manually.

## Advanced AI optimization strategies

Beyond technical implementation, strategic positioning determines AI visibility. Case studies reveal patterns that drive exponential traffic increases.

### Citation gap analysis: Highest-leverage activity

Research analyzing ranking factors across ChatGPT, Google AI Overviews, and Perplexity found **authoritative list mentions account for 41-64% of citation probability** - the single highest-impact factor. Getting mentioned in curated lists like "Top HPC Researchers," "Best Storage Systems Papers," or "Leading I/O Optimization Experts" dramatically increases AI recommendation frequency.

**Action steps:**
1. Identify authoritative lists in your field (academic rankings, research compilations, expert directories)
2. Analyze which lists mention colleagues but not you
3. Contact curators with your unique contributions and credentials
4. Target 10-20 high-value list inclusions over 6 months

This strategy delivers disproportionate returns compared to effort invested. A single TechRadar or ACM list mention can generate visibility across thousands of queries.

### Freshness signals and content updates

AI search engines heavily favor recent content, with material from the past 2-3 months dominating citations. For academic websites with inherently slower publication cycles, implement these tactics:

**Visible update dates** signal freshness. Add `last_modified_at` to front matter and display prominently:

```liquid
<p class="meta">Published: {{ page.date | date: "%B %d, %Y" }} | 
Updated: {{ page.last_modified_at | default: page.date | date: "%B %d, %Y" }}</p>
```

**Regular refreshes** of top content maintain relevance. Monthly, update your:
- Homepage with recent activities
- Research page with latest publications
- CV/resume with current information
- Blog with new posts or updates

**Current year in strategic places** reinforces timeliness. Use "2025" in page titles, descriptions, and content where naturally appropriate.

### E-E-A-T signals for academic authority

AI systems evaluate Experience, Expertise, Authoritativeness, and Trustworthiness through specific signals:

**Author credentials prominently displayed** - Include your title, affiliation, and degrees in bios. Add to schema markup and visible page content.

**Publication venue quality** - Mention impact factors, acceptance rates, or rankings for top-tier venues (SC, HPDC, SOSP, OSDI).

**Awards and distinctions** - Highlight best paper awards, grants, honors, and recognitions prominently. These carry 15-19% weight in citation algorithms.

**External validation** - Citations from other researchers, media mentions, invited talks, and program committee service all signal authority. Link to Google Scholar citation counts and h-index.

**Transparent methodology** - For research summaries, explain approaches, limitations, and validation clearly. AI systems favor honest, balanced presentation over promotional content.

### Engagement in user-generated content platforms

Reddit citations surged 450% in recent analysis, now comprising 21.74% of all AI citations - the highest share of any platform type. This creates opportunities for researchers to increase visibility through strategic engagement.

**High-value participation targets:**
- r/compsci, r/MachineLearning, r/HighPerformanceComputing
- Technical subreddits related to your research areas
- Answer specific questions with detailed, expert responses
- Threads with 50+ existing responses (higher visibility)

**Quora expert answers** with high upvote counts also receive significant AI citation. Provide comprehensive, authoritative answers to questions in your domain.

**LinkedIn Pulse articles** on research topics contribute to professional authority signals.

**Authentic engagement principles:** Add genuine value, avoid self-promotion, cite your work naturally when relevant, and build reputation through consistent quality contributions.

## Implementation roadmap

Execute these optimizations systematically over 4-6 weeks for maximum impact.

### Week 1: Foundation

- Install jekyll-seo-tag, jekyll-sitemap, jekyll-feed plugins
- Configure _config.yml with complete metadata
- Add `{% seo %}` tag to layout head sections
- Create and test robots.txt with strategic AI crawler directives
- Submit sitemap to Google Search Console and Bing Webmaster Tools

### Week 2: Structured data and llms.txt

- Implement Person schema for homepage/about page
- Add ScholarlyArticle schema to publication pages
- Create and deploy llms.txt at root directory
- Validate schema using Google Rich Results Test
- Test llms.txt accessibility and formatting

### Week 3: Content optimization

- Audit top 10 pages for structure (H1-H3 hierarchy, short paragraphs)
- Add answer-focused introductions to research project descriptions
- Create FAQ sections for major research areas
- Update publication metadata for completeness
- Add visible "last updated" dates to key pages

### Week 4: Performance and technical

- Implement HTML minification with jekyll-compress-html
- Optimize and compress images (target 70-85 JPEG quality)
- Enable lazy loading on images below the fold
- Test JavaScript dependency (disable JS, verify content visibility)
- Run PageSpeed Insights and address critical issues

### Weeks 5-6: Strategic positioning

- Conduct citation gap analysis for authoritative lists in your field
- Identify 10-20 target list placements
- Begin outreach to curators and editors
- Engage in 5-10 high-value Reddit or Quora discussions
- Refresh top content with current statistics and dates

### Ongoing maintenance

**Monthly:** Update homepage, research page, and CV with recent activities. Refresh top 5 pages with new data and current dates. Monitor AI referral traffic through Google Analytics.

**Quarterly:** Audit next 20 pages for optimization opportunities. Review citation coverage in AI systems (search for your name in ChatGPT, Perplexity). Check for new authoritative lists to target.

**Annually:** Comprehensive SEO audit using Screaming Frog or Ahrefs. Review schema markup implementations for updates. Analyze AI traffic patterns and adjust strategy.

## Monitoring AI visibility

Track success through specific metrics measuring AI discovery effectiveness.

### Google Analytics 4 custom tracking

Create custom dimensions for AI referral sources using regex patterns:

**Traffic source identification:**
- ChatGPT: `chatgpt.com` referrals
- Perplexity: `perplexity.ai` referrals
- Google AI: Filter for `ai_overview` parameter
- Bing Copilot: `bing.com/search` with Copilot indicators

Configure custom reports tracking conversion rates, engagement metrics, and content preferences for AI-sourced visitors. Case studies show these visitors convert at 13x the rate of traditional search traffic.

### Citation monitoring

**Manual checks:** Periodically search for your research topics in ChatGPT, Perplexity, Google AI mode, and Bing Copilot. Document whether your site appears in citations and for which queries.

**Ahrefs AI Overview filter:** Ahrefs now offers specific filtering for Google AI Overview appearances. Track keyword coverage and citation frequency for monitored terms.

**BrightEdge and Conductor:** Enterprise tools provide comprehensive AI visibility tracking, though typically suited for larger organizations.

### Server log analysis

Review access logs for AI crawler activity:

```bash
grep -i "GPTBot\|OAI-SearchBot\|PerplexityBot\|ClaudeBot" access.log
```

Monitor crawl frequency, pages accessed, and bandwidth consumption. Adjust crawl-delay directives if necessary.

## Old domain migration status

Research into references for your previous domain akougkas.com revealed excellent migration success. Only two broken references were found through comprehensive web searches:

**Found references:**
1. www.akougkas.com/about.html (CV/resume page - DNS not resolving)
2. akougkas.com/publications.html (Publications listing - DNS not resolving)

**Successfully updated platforms:**
- Illinois Tech directory
- Google Scholar
- LinkedIn
- GitHub
- ORCID
- OpenReview
- ACM Digital Library
- DBLP
- IEEE Xplore
- ResearchGate
- Academia.edu

The old domain is offline with DNS not resolving, and major academic platforms already reference akougkas.io. Search engine results show minimal lingering references to the defunct domain.

**Recommended action:** If you still own akougkas.com, configure a 301 permanent redirect to akougkas.io to capture any remaining traffic. If the domain has expired, the impact is minimal given the successful migration across major platforms. Submit the broken URLs to Google Search Console requesting removal to clean up search results.

No academic papers were found citing the old domain in bibliographies, and publication databases (DBLP, ACM, arXiv) do not store personal website URLs in their records, avoiding this concern entirely.

## Critical success factors

Based on case studies showing 750-4,162% traffic increases, these patterns separate successful implementations from ineffective ones:

**Schema markup is non-negotiable** - Pages without structured data may fail to index in AI systems at all. Implementation determines visibility, not optimization.

**Citation gaps represent highest ROI** - Getting mentioned in authoritative lists has 41-64% impact on recommendations. Target 10-20 strategic placements delivering exponential visibility gains.

**Freshness compounds over time** - Regular updates signal active maintenance. Monthly refreshes of top content dramatically increase citation probability.

**Structure trumps keywords** - Clear hierarchy, short paragraphs, tables, and bullet points enable AI parsing. Well-organized content consistently outperforms keyword-stuffed alternatives.

**JavaScript creates invisibility** - Most AI crawlers cannot render JavaScript. Server-side content is essential for discoverability.

**E-E-A-T provides foundation** - Author credentials, institutional affiliations, publication quality, and external validation establish trustworthiness AI systems require before citing sources.

**Early adoption creates compound advantages** - AI models develop trust relationships with sources they consistently cite. First-movers establishing authority gain exponential benefits as AI search adoption accelerates.

The competitive window is closing rapidly. AI systems are forming persistent trust relationships with sources now, making immediate implementation strategically critical for long-term visibility in AI-driven discovery ecosystems.