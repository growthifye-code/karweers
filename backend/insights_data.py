"""Topic plan + curated image pools for the per-service Insights engine.

Each service gets 10 consulting-grade blog topics spanning six categories:
Current Practice, Case Study, Deal Learning, AI & Technology, Strategy Success, Strategy Failure.
Topics reference real, public-domain companies/deals so the LLM can write grounded analysis.
"""

# Brand editorial illustrations (obsidian + lime), generated for this platform.
EDITORIAL = {
    "strategy": "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/7f125a1f1458fd219442185ba8c28ef636065a3b54483dc7a928dfa2f3736d8a.jpeg",
    "ai": "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/10ca2db0800a8997494a0c1f38ccb8255421d25acfe48d307db12795f2dc007b.jpeg",
    "deal": "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/97d038b8bbf3ad5c3b148be281a77b4bbfbcdf94dfc5d0eb24e5cfe9a200daf6.jpeg",
    "energy": "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/c49a68ed5e72243d733bdf6137b9324f85cb21ea6b4d2cc17a662820add2d56d.jpeg",
}

# Real stock photography per service theme.
_STRATEGY_IMGS = [
    "https://images.unsplash.com/photo-1758518730037-a16581a040e8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1769740333462-9a63bfa914bc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1758691736424-4b4273948341?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1769739576456-0aefcff3f4b9?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_DEAL_IMGS = [
    "https://images.unsplash.com/photo-1758599543152-a73184816eba?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1758518729240-7162d07427b8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1752159646124-27b7f6973be8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1758599543278-32d9d073941e?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_CAPITAL_IMGS = [
    "https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1745270917449-c2e2c5806586?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1649003515353-c58a239cf662?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1738737271801-d404a575d870?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_COACH_IMGS = [
    "https://images.unsplash.com/photo-1577962917302-cd874c4e31d2?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1681949287382-052ea3954a51?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1675716921224-e087a0cca69a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_ENERGY_IMGS = [
    "https://images.unsplash.com/photo-1509391366360-2e959784a276?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1558449028-b53a39d100fc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1613665813446-82a78c468a1d?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_GREEN_IMGS = [
    "https://images.unsplash.com/photo-1467533003447-e295ff1b0435?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1594389615321-4f50c5d7878c?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1598298809876-32b6a79f716a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1472313420546-a46e561861d8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]
_INFRA_IMGS = [
    "https://images.unsplash.com/photo-1713576498357-4a0ef29388cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1536099629323-44806c1ea264?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1715199325812-b5d467797838?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
    "https://images.unsplash.com/photo-1633627290885-0461dd93e8a2?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400",
]

# Per-service hero pool = thematic stock + a brand editorial accent.
IMAGE_POOLS = {
    "business-strategy": _STRATEGY_IMGS + [EDITORIAL["strategy"]],
    "ma-advisory": _DEAL_IMGS + [EDITORIAL["deal"]],
    "fund-raising": _CAPITAL_IMGS + [EDITORIAL["deal"]],
    "premium-consultation": _COACH_IMGS + [EDITORIAL["strategy"]],
    "re-storage-hydrogen": _ENERGY_IMGS + [EDITORIAL["energy"]],
    "green-climate-financing": _GREEN_IMGS + [EDITORIAL["energy"]],
    "asset-monetisation": _INFRA_IMGS + [EDITORIAL["deal"]],
    "business-coaching": _COACH_IMGS + [EDITORIAL["strategy"]],
}

CATEGORIES = ["Current Practice", "Case Study", "Deal Learning",
              "AI & Technology", "Strategy Success", "Strategy Failure"]

# 10 topics per service. (slug auto-derived from title.)
TOPIC_PLAN = {
    "business-strategy": [
        ("The New Rules of Corporate Strategy: From Five-Year Plans to Rolling Bets", "Current Practice"),
        ("Titan: How a Watch Company Became a Lifestyle Empire", "Strategy Success"),
        ("Nokia and Kodak: The Anatomy of Watching Your Own Disruption", "Strategy Failure"),
        ("Reliance's New-Energy Pivot: Reading a Multi-Billion-Dollar Strategic Bet", "Case Study"),
        ("AI in the Boardroom: Where Machine Intelligence Actually Changes Strategy", "AI & Technology"),
        ("Zomato vs Swiggy: Two Strategies in India's Food-Delivery War", "Case Study"),
        ("Portfolio Strategy: How Great Companies Decide What to Kill", "Current Practice"),
        ("Tata-Corus: When a Trophy Acquisition Became a Balance-Sheet Anchor", "Deal Learning"),
        ("Market Entry Without Bleeding: A Modern Framework", "Current Practice"),
        ("Vodafone Idea: How Incumbents Lose to a Better-Capitalised Insurgent", "Strategy Failure"),
    ],
    "ma-advisory": [
        ("Disney-Fox: Paying a Premium for Scale in a Streaming War", "Deal Learning"),
        ("AOL-Time Warner: The Merger That Defined Value Destruction", "Strategy Failure"),
        ("Microsoft-LinkedIn: A $26bn Deal That Actually Worked", "Strategy Success"),
        ("HDFC-HDFC Bank: The Logic Behind India's Largest Merger", "Case Study"),
        ("Integration Is the Deal: The First 100 Days That Decide Value", "Current Practice"),
        ("AI in Due Diligence: Faster, Deeper, and the New Risks", "AI & Technology"),
        ("Vodafone-Idea: When a Defensive Merger Leaves Both Weaker", "Deal Learning"),
        ("Air India Returns to Tata: A Turnaround and Loyalty-Asset Play", "Case Study"),
        ("Adani's Acquisition Machine: The Cement Consolidation Play", "Strategy Success"),
        ("Carve-Outs and Loyalty Monetisation: Unlocking Hidden Asset Value", "Current Practice"),
    ],
    "fund-raising": [
        ("WeWork: How a $47bn Story Collapsed at the IPO Door", "Case Study"),
        ("Zomato's IPO: Pricing Growth Without a Profit Story", "Strategy Success"),
        ("Byju's: When Capital Outran Governance", "Deal Learning"),
        ("Capital Readiness: The Quarters Before the Raise Decide the Terms", "Current Practice"),
        ("AI-Era Fundraising: What Investors Now Underwrite in a Tech Story", "AI & Technology"),
        ("Reliance Jio Platforms: Raising Over $20bn in a Pandemic", "Case Study"),
        ("Paytm's IPO: A Lesson in Valuation vs Fundamentals", "Strategy Failure"),
        ("Green Bonds and Blended Finance: Structuring Bankable Climate Capital", "Deal Learning"),
        ("Building a Data Room That Closes Rounds", "Current Practice"),
        ("Tesla's Capital Journey: Funding an Industry Into Existence", "Strategy Success"),
    ],
    "premium-consultation": [
        ("The Real Question Behind the Question: How Executives Get Un-Stuck", "Current Practice"),
        ("Satya Nadella's Reset: Diagnosing and Rebuilding a Culture", "Case Study"),
        ("The Turnaround Playbook: What Great Leaders Do in the First 90 Days", "Strategy Success"),
        ("GE Under Immelt: When Complexity Became the Strategy", "Strategy Failure"),
        ("The AI-Augmented Executive: Decisions Machines Should and Shouldn't Touch", "AI & Technology"),
        ("Boeing's 737 MAX: When Financial Pressure Overrode Engineering Judgement", "Deal Learning"),
        ("Decision-Making Under Uncertainty: Options Over Forecasts", "Current Practice"),
        ("Netflix's Two Bets: Streaming and Original Content", "Case Study"),
        ("How Domino's Rebuilt a Brand by Admitting It Was Failing", "Strategy Success"),
        ("The Discipline of Saying No: Focus for Overextended Leaders", "Current Practice"),
    ],
    "re-storage-hydrogen": [
        ("India's BESS Inflection: The Economics of Grid-Scale Storage", "Case Study"),
        ("Right-Sizing a Renewable Project: Where Developers Destroy Returns", "Current Practice"),
        ("Adani Green and ReNew: Two Models for Scaling Renewables", "Deal Learning"),
        ("AI in Grid and Asset Optimisation: The New Alpha in Energy", "AI & Technology"),
        ("Green Hydrogen's Hype Cycle: Bankable vs Aspirational", "Strategy Failure"),
        ("NTPC's Green Transition: A Coal Giant's Strategic Hedge", "Case Study"),
        ("The Revenue Stack: Designing Offtake for Storage and Hybrid Assets", "Current Practice"),
        ("Orsted: From Oil & Gas to the World's Largest Offshore Wind Player", "Strategy Success"),
        ("First Solar vs the Commodity Trap: Technology as a Moat", "Strategy Success"),
        ("Digital Twins and Predictive Maintenance in Energy Assets", "AI & Technology"),
    ],
    "green-climate-financing": [
        ("Blended Finance: Making Marginal Climate Projects Bankable", "Current Practice"),
        ("Sovereign Green Bonds: India's Entry and What It Signals", "Case Study"),
        ("The Rise and Reckoning of ESG Investing", "Deal Learning"),
        ("AI for Climate Risk: Pricing Physical and Transition Risk", "AI & Technology"),
        ("How Brookfield Built a Climate-Transition Capital Machine", "Strategy Success"),
        ("Carbon Markets: Structuring Credible, Fundable Offsets", "Current Practice"),
        ("IREDA and Development-Bank Capital in India's Green Build-Out", "Case Study"),
        ("Greenwashing's Legal Turn: When Climate Claims Become Liabilities", "Deal Learning"),
        ("Concessional Capital Gone Wrong: When Cheap Money Funds Bad Projects", "Strategy Failure"),
        ("The Bankability Checklist for Climate Infrastructure", "Current Practice"),
    ],
    "asset-monetisation": [
        ("The National Monetisation Pipeline: India's Multi-Lakh-Crore Asset Play", "Case Study"),
        ("Monetising Without Privatising: The InvIT and TOT Toolkit", "Current Practice"),
        ("MSRTC Bus Depots: Unlocking Land Value from Transport Assets", "Deal Learning"),
        ("PowerGrid InvIT: A Template for Recycling Infrastructure Capital", "Strategy Success"),
        ("Digitising Public Assets: Data as a Monetisable Layer", "AI & Technology"),
        ("Airport Monetisation: The Concession Playbook", "Case Study"),
        ("Highway Monetisation via Toll-Operate-Transfer: Getting Pricing Right", "Current Practice"),
        ("Railways and Station Redevelopment: Value Capture Done Right", "Deal Learning"),
        ("When Monetisation Fails: Lessons from Stalled Disinvestments", "Strategy Failure"),
        ("Structuring a Depot or Land Asset for Maximum Value", "Current Practice"),
    ],
    "business-coaching": [
        ("From Founder to CEO: The Hardest Transition in Business", "Current Practice"),
        ("How Satya Nadella Coached a Growth Mindset Into Microsoft", "Case Study"),
        ("Building Leaders Who Scale: Lessons from India's Best Operators", "Strategy Success"),
        ("The AI-Augmented Leader: Coaching in the Age of Machine Intelligence", "AI & Technology"),
        ("Founder's Syndrome: When the Strength Becomes the Ceiling", "Strategy Failure"),
        ("The Executive Operating Rhythm: Cadence That Compounds", "Current Practice"),
        ("Turnaround Leadership: What Changed at Domino's and Lego", "Case Study"),
        ("Succession Done Right: The Tata and Infosys Contrast", "Deal Learning"),
        ("Difficult Conversations: The Coaching Skill Every CXO Needs", "Current Practice"),
        ("Scaling Culture: How High-Growth Firms Keep Their Edge", "Strategy Success"),
    ],
}


def hero_for(service_slug: str, category: str, index: int) -> str:
    """Pick a hero image: AI editorial for tech pieces, else cycle the service pool."""
    if category == "AI & Technology":
        return EDITORIAL["ai"]
    pool = IMAGE_POOLS.get(service_slug) or _STRATEGY_IMGS
    return pool[index % len(pool)]
