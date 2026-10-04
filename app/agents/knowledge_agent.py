import re

from app.schemas import Article, KnowledgeItem

VOCABULARY = {
    "companies": ["OpenAI", "Google", "Microsoft", "Apple", "Meta", "Amazon", "Nvidia", "Anthropic", "Samsung", "Intel", "AMD", "Tesla", "Linux Foundation"],
    "technologies": ["artificial intelligence", "AI", "cloud", "cybersecurity", "machine learning", "LLM", "robotics", "quantum computing", "blockchain", "GPU"],
    "programming_languages": ["Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "C++", "Swift", "Kotlin"],
    "frameworks": ["React", "LangChain", "LangGraph", "PyTorch", "TensorFlow", "Django", "Kubernetes", "Next.js", "Node.js"],
}
CATEGORY_TERMS = {
    "AI": ["ai", "artificial intelligence", "machine learning", "llm", "model"],
    "Programming": ["programming", "developer", "code", "python", "javascript", "software"],
    "Cloud": ["cloud", "aws", "azure", "google cloud"],
    "Cybersecurity": ["security", "hack", "breach", "vulnerability", "malware"],
    "Open Source": ["open source", "github", "linux"],
    "Mobile": ["iphone", "android", "mobile", "smartphone"],
    "Hardware": ["chip", "gpu", "device", "hardware", "processor"],
    "Startups": ["startup", "funding", "venture", "raises"],
    "Big Tech": ["google", "microsoft", "apple", "meta", "amazon", "nvidia"],
    "Developer Tools": ["developer tool", "framework", "api", "sdk"],
    "Robotics": ["robot", "robotics", "automation"],
}


def _matches(text: str, terms: list[str]) -> list[str]:
    low = text.lower()
    return [term for term in terms if re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", low)]


def build_knowledge(articles: list[Article]) -> list[KnowledgeItem]:
    items = []
    for article in articles:
        text = f"{article.title}. {article.content}"
        low = text.lower()
        categories = [name for name, terms in CATEGORY_TERMS.items() if any(term in low for term in terms)]
        companies = _matches(text, VOCABULARY["companies"])
        tech = _matches(text, VOCABULARY["technologies"])
        languages = _matches(text, VOCABULARY["programming_languages"])
        frameworks = _matches(text, VOCABULARY["frameworks"])
        people = list(dict.fromkeys(  # conservative capitalized-name extraction
            match for match in re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", article.content)
            if match not in companies
        ))[:10]
        items.append(KnowledgeItem(
            topic=article.title, category=categories[0] if categories else "Technology",
            companies=companies, people=people, products=[], technologies=tech,
            programming_languages=languages, frameworks=frameworks,
            important_events=[article.title], keywords=list(dict.fromkeys(tech + languages + frameworks + companies))[:20],
            article_url=str(article.url),
        ))
    return items
