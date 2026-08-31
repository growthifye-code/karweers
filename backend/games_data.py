"""CXO Strategy Simulations — original scenario "war-room" games.

Each game teaches a leadership framework through a series of decisions. Every
option carries a score (0-3) and immediate feedback. The final debrief and key
lessons are written in Sudarshan Karweer's advisory voice. All scenarios are
original; framework names are credited to their authors for learning context.
"""

GAMES = [
    {
        "slug": "art-of-war",
        "title": "The Contested Market",
        "framework": "The Art of War",
        "author": "after Sun Tzu",
        "icon": "swords",
        "tag": "Strategy",
        "blurb": "A larger rival is moving into your market. Win position without a bloody price war.",
        "intro": "You run a profitable regional player. A national competitor with deeper pockets has just announced entry into your core city. The board is nervous. You have one quarter to set your line. Sun Tzu's counsel: win before you fight.",
        "rounds": [
            {"id": 1, "situation": "The rival announces aggressive pricing to grab share fast.",
             "question": "Your opening move?",
             "options": [
                 {"id": "a", "text": "Match their price cut across the board immediately.", "score": 0,
                  "feedback": "You've entered a war of attrition against a bigger balance sheet — exactly the fight Sun Tzu says to avoid."},
                 {"id": "b", "text": "Hold price; quietly map where they're weakest before reacting.", "score": 3,
                  "feedback": "Know the ground and the enemy first. You buy time and information before committing force."},
                 {"id": "c", "text": "Announce an even deeper cut to look strong.", "score": 1,
                  "feedback": "Bravado burns cash. Looking strong and being strong are different things."}]},
            {"id": 2, "situation": "You learn the rival's supply chain is stretched serving the whole country.",
             "question": "How do you use this?",
             "options": [
                 {"id": "a", "text": "Attack them nationally with a PR campaign.", "score": 0,
                  "feedback": "You've picked a fight on their terrain, where they're strongest."},
                 {"id": "b", "text": "Lock in your best local suppliers on exclusivity now.", "score": 3,
                  "feedback": "Deny the enemy the ground they need. You turn their scale into a weakness."},
                 {"id": "c", "text": "Do nothing; wait to see their next move.", "score": 1,
                  "feedback": "Patience is good, but a known weakness left unused is an opportunity wasted."}]},
            {"id": 3, "situation": "Your top three customers are being courted with sweeteners.",
             "question": "Your play for your base?",
             "options": [
                 {"id": "a", "text": "Deepen relationships and multi-year value with your top accounts.", "score": 3,
                  "feedback": "Fortify what's most valuable. Defended ground is cheaper to hold than to retake."},
                 {"id": "b", "text": "Spread thin discounts to every customer equally.", "score": 1,
                  "feedback": "You dilute force everywhere and hold nowhere strongly."},
                 {"id": "c", "text": "Assume loyalty will hold and focus elsewhere.", "score": 0,
                  "feedback": "Complacency loses your most important terrain."}]},
            {"id": 4, "situation": "A niche the rival ignores is growing quietly.",
             "question": "Do you move on it?",
             "options": [
                 {"id": "a", "text": "Take the uncontested niche decisively and own it.", "score": 3,
                  "feedback": "The supreme art: win where there is no battle. Uncontested ground is the cheapest to hold."},
                 {"id": "b", "text": "Note it, but stay focused on defending the core.", "score": 1,
                  "feedback": "Reasonable, but you leave growth on the table a rival could later take."},
                 {"id": "c", "text": "Ignore it as too small.", "score": 0,
                  "feedback": "Small today, contested tomorrow. Sun Tzu prizes ground others overlook."}]},
            {"id": 5, "situation": "The rival, over-extended, signals openness to a truce in your city.",
             "question": "Your response?",
             "options": [
                 {"id": "a", "text": "Press the advantage and try to destroy them entirely.", "score": 0,
                  "feedback": "A cornered enemy fights hardest. Total war costs you more than it's worth."},
                 {"id": "b", "text": "Accept a rational détente that protects your position.", "score": 3,
                  "feedback": "Subdue the rival without a battle. You keep your city and your margins intact."},
                 {"id": "c", "text": "Ignore the signal and keep fighting on instinct.", "score": 1,
                  "feedback": "Momentum feels good but a winning exit is a skill of its own."}]},
        ],
        "lessons": ["Win before you fight — gather information before you commit resources.",
                    "Never fight on the enemy's strongest ground; find and use their weakness.",
                    "Fortify your most valuable customers; defended ground is cheap to hold.",
                    "The cheapest victories are in the markets no one is contesting.",
                    "Know when to accept a good peace — a clean win beats an endless war."],
    },
    {
        "slug": "extreme-ownership",
        "title": "The Missed Deadline",
        "framework": "Extreme Ownership",
        "author": "after Willink & Babin",
        "icon": "shield",
        "tag": "Ownership",
        "blurb": "A flagship launch just slipped. How you respond defines you as a leader.",
        "intro": "Your team missed a launch the CEO promised the board. Fingers are already pointing. As the leader, everything in your world is your responsibility — including this.",
        "rounds": [
            {"id": 1, "situation": "In the post-mortem, the room waits to see how you'll open.",
             "question": "Your first words?",
             "options": [
                 {"id": "a", "text": "'This is on me. I didn't set the plan up to succeed.'", "score": 3,
                  "feedback": "Extreme ownership starts at the top. When the leader owns it, the team stops hiding and starts fixing."},
                 {"id": "b", "text": "'Engineering under-delivered — let's hear from them.'", "score": 0,
                  "feedback": "Blame down and the team learns to protect itself, not to improve."},
                 {"id": "c", "text": "'These things happen; let's just move on.'", "score": 1,
                  "feedback": "Avoiding accountability guarantees a repeat."}]},
            {"id": 2, "situation": "You discover the spec was genuinely ambiguous.",
             "question": "What does that tell you?",
             "options": [
                 {"id": "a", "text": "The team should have asked more questions.", "score": 0,
                  "feedback": "If they didn't understand, you didn't communicate it clearly enough. That's a leadership miss."},
                 {"id": "b", "text": "I failed to make the intent simple and clear.", "score": 3,
                  "feedback": "Keep it simple. If the team was confused, the leader owns the clarity."},
                 {"id": "c", "text": "Specs are always ambiguous; nothing to learn.", "score": 1,
                  "feedback": "There's always a lesson if you look for it."}]},
            {"id": 3, "situation": "The CEO asks who's responsible.",
             "question": "Your answer?",
             "options": [
                 {"id": "a", "text": "'I am. Here's my plan to fix it.'", "score": 3,
                  "feedback": "Own it upward, then lead with a plan. Credibility is built in exactly these moments."},
                 {"id": "b", "text": "Name the individuals involved.", "score": 0,
                  "feedback": "Throwing people under the bus destroys trust and your own standing."},
                 {"id": "c", "text": "'It was a team effort that fell short.'", "score": 1,
                  "feedback": "Vague ownership is no ownership. Be specific: it's yours."}]},
            {"id": 4, "situation": "You must re-plan under pressure with many competing fires.",
             "question": "How do you run it?",
             "options": [
                 {"id": "a", "text": "Prioritise and execute — attack the single biggest risk first.", "score": 3,
                  "feedback": "When everything's urgent, nothing is. Handle the highest threat, then the next."},
                 {"id": "b", "text": "Ask everyone to work on everything harder.", "score": 0,
                  "feedback": "Effort without priority just spreads the team thin and burns them out."},
                 {"id": "c", "text": "Wait for perfect information before acting.", "score": 1,
                  "feedback": "Decisiveness under uncertainty is the job. Perfect information never comes."}]},
            {"id": 5, "situation": "You set up the recovery so it can't happen again.",
             "question": "Best structural fix?",
             "options": [
                 {"id": "a", "text": "Micro-manage every step yourself from now on.", "score": 0,
                  "feedback": "You become the bottleneck. That's the opposite of decentralised command."},
                 {"id": "b", "text": "Give teams clear intent and authority to act on it.", "score": 3,
                  "feedback": "Decentralised command: everyone understands the why and can decide in the moment."},
                 {"id": "c", "text": "Add three more approval layers.", "score": 1,
                  "feedback": "More gates slow you down and dilute ownership."}]},
        ],
        "lessons": ["When the leader owns the failure, the team stops defending and starts fixing.",
                    "If the team was confused, the leader failed to make the intent clear.",
                    "Own it upward — always pair accountability with a plan.",
                    "Prioritise and execute: attack the highest-priority threat first.",
                    "Decentralise command: clear intent plus authority beats micro-management."],
    },
    {
        "slug": "team-trust",
        "title": "The Silent Team",
        "framework": "The Five Dysfunctions of a Team",
        "author": "after Patrick Lencioni",
        "icon": "users",
        "tag": "Team Health",
        "blurb": "A talented team that never disagrees is quietly failing. Rebuild it from trust up.",
        "intro": "You've inherited a smart, polite team that always 'agrees' in the room — then misses commitments after. Lencioni's pyramid starts at the bottom: without trust, nothing above it works.",
        "rounds": [
            {"id": 1, "situation": "Meetings are calm, agreeable and strangely lifeless.",
             "question": "Your read on the root cause?",
             "options": [
                 {"id": "a", "text": "They lack trust, so they avoid real conflict.", "score": 3,
                  "feedback": "Correct. Artificial harmony is the tell-tale sign of absent trust."},
                 {"id": "b", "text": "They just need clearer agendas.", "score": 1,
                  "feedback": "Process helps, but it won't fix a trust problem underneath."},
                 {"id": "c", "text": "They're aligned and high-performing.", "score": 0,
                  "feedback": "Silence isn't alignment. It's often fear."}]},
            {"id": 2, "situation": "You want to build trust first.",
             "question": "What do you do?",
             "options": [
                 {"id": "a", "text": "Go first: openly admit your own recent mistake.", "score": 3,
                  "feedback": "Vulnerability-based trust starts with the leader. You make it safe to be human."},
                 {"id": "b", "text": "Run a personality workshop and move on.", "score": 1,
                  "feedback": "A start, but trust is built by repeated behaviour, not a one-off session."},
                 {"id": "c", "text": "Tell them to 'just trust each other'.", "score": 0,
                  "feedback": "Trust can't be ordered. It's modelled and earned."}]},
            {"id": 3, "situation": "A real disagreement finally surfaces in a meeting.",
             "question": "How do you handle it?",
             "options": [
                 {"id": "a", "text": "Encourage the debate and mine for the best answer.", "score": 3,
                  "feedback": "Productive conflict is the goal, not the problem. Good decisions need it."},
                 {"id": "b", "text": "Smooth it over quickly to keep the peace.", "score": 0,
                  "feedback": "You just taught them conflict is unwelcome — back to artificial harmony."},
                 {"id": "c", "text": "Let it turn personal to 'clear the air'.", "score": 1,
                  "feedback": "Conflict must stay about ideas, not people. Guardrails matter."}]},
            {"id": 4, "situation": "A decision is made, but two people clearly still disagree.",
             "question": "Your move?",
             "options": [
                 {"id": "a", "text": "Get explicit commitment: disagree and commit.", "score": 3,
                  "feedback": "People commit to decisions they had a voice in — even ones they'd have made differently."},
                 {"id": "b", "text": "Reopen the debate indefinitely until all agree.", "score": 1,
                  "feedback": "Consensus-seeking stalls teams. Buy-in, not unanimity, is the aim."},
                 {"id": "c", "text": "Ignore their body language and move on.", "score": 0,
                  "feedback": "Unspoken dissent becomes quiet sabotage later."}]},
            {"id": 5, "situation": "A peer is missing shared commitments again.",
             "question": "Who should address it?",
             "options": [
                 {"id": "a", "text": "Only you, privately, as the boss.", "score": 1,
                  "feedback": "Better than nothing, but healthy teams hold each other accountable."},
                 {"id": "b", "text": "Encourage peers to call it out directly and respectfully.", "score": 3,
                  "feedback": "Peer accountability is the mark of a mature team — and it keeps everyone honest to results."},
                 {"id": "c", "text": "Let it slide to avoid tension.", "score": 0,
                  "feedback": "Tolerating missed commitments lowers the standard for everyone."}]},
        ],
        "lessons": ["Artificial harmony signals absent trust — silence is not alignment.",
                    "Vulnerability-based trust starts with the leader going first.",
                    "Productive conflict about ideas produces better decisions than polite agreement.",
                    "Aim for buy-in, not unanimity: disagree and commit.",
                    "Mature teams hold each other accountable to results, not just the boss."],
    },
    {
        "slug": "hiring",
        "title": "The Hiring Call",
        "framework": "First Who, Then What",
        "author": "after Jim Collins & modern hiring practice",
        "icon": "user-check",
        "tag": "Hiring",
        "blurb": "One senior seat, three flawed finalists, and huge pressure to fill it fast.",
        "intro": "A critical leadership seat has been empty for months and the pressure to fill it is intense. Great companies get the right people on the bus first. A wrong senior hire is one of the most expensive mistakes you can make.",
        "rounds": [
            {"id": 1, "situation": "A brilliant candidate aced the skills test but two references hint at ego and blame.",
             "question": "How much weight do you give the references?",
             "options": [
                 {"id": "a", "text": "Skills win; ignore the soft signals.", "score": 0,
                  "feedback": "At senior level, character and how they treat people outlast raw skill. You're buying behaviour."},
                 {"id": "b", "text": "Dig deeper — a values misfit in a leader is a culture risk.", "score": 3,
                  "feedback": "Right. A toxic senior hire damages far more than one role's output."},
                 {"id": "c", "text": "Hire fast; you'll coach the behaviour later.", "score": 1,
                  "feedback": "You rarely coach out a senior leader's core temperament. Hire for it."}]},
            {"id": 2, "situation": "The pressure to fill the seat this week is enormous.",
             "question": "Your stance?",
             "options": [
                 {"id": "a", "text": "Settle for the best available to stop the bleeding.", "score": 0,
                  "feedback": "'When in doubt, don't hire.' A wrong senior hire costs more than an empty seat."},
                 {"id": "b", "text": "Keep the bar; bridge the gap with an interim.", "score": 3,
                  "feedback": "Protecting the bar under pressure is exactly when it matters most."},
                 {"id": "c", "text": "Lower the spec to widen the pool.", "score": 1,
                  "feedback": "Sometimes valid — but not as a reflex to relieve pressure."}]},
            {"id": 3, "situation": "A strong candidate wants far more than the band allows.",
             "question": "What do you do?",
             "options": [
                 {"id": "a", "text": "Break the band quietly to land them.", "score": 0,
                  "feedback": "Pay inequity leaks and corrodes trust across the whole team."},
                 {"id": "b", "text": "Be transparent on band; sell growth, ownership and mission.", "score": 3,
                  "feedback": "The right people are moved by mission and autonomy, not only cash."},
                 {"id": "c", "text": "Walk away instantly over the number.", "score": 1,
                  "feedback": "Explore the full offer first; money is one lever of several."}]},
            {"id": 4, "situation": "Your gut says 'maybe' after all interviews.",
             "question": "How do you treat a 'maybe'?",
             "options": [
                 {"id": "a", "text": "A 'maybe' is a 'no' for a key hire.", "score": 3,
                  "feedback": "For senior seats, conviction matters. Ambivalence now becomes regret later."},
                 {"id": "b", "text": "A 'maybe' is a 'yes' — take the chance.", "score": 0,
                  "feedback": "Hope is not a hiring strategy at this level."},
                 {"id": "c", "text": "Flip a coin; you're out of time.", "score": 1,
                  "feedback": "Randomness on a pivotal seat is an avoidable risk."}]},
            {"id": 5, "situation": "You've made the hire. First 90 days.",
             "question": "How do you set them up?",
             "options": [
                 {"id": "a", "text": "Clear charter, early wins and honest feedback loop.", "score": 3,
                  "feedback": "Onboarding is where good hires become great — or quietly derail."},
                 {"id": "b", "text": "Throw them in; sink or swim.", "score": 0,
                  "feedback": "You just wasted your careful selection with a careless start."},
                 {"id": "c", "text": "Leave them alone to 'not micromanage'.", "score": 1,
                  "feedback": "Autonomy needs a clear charter first, or it's just abandonment."}]},
        ],
        "lessons": ["At senior level you hire behaviour and values, not just skills.",
                    "When in doubt, don't hire — a wrong senior hire costs more than an empty seat.",
                    "Sell mission, ownership and growth; protect pay equity across the team.",
                    "For pivotal seats, a 'maybe' is a 'no' — conviction matters.",
                    "Onboarding with a clear charter and early wins makes the hire succeed."],
    },
    {
        "slug": "financial-management",
        "title": "Cash & Runway",
        "framework": "Cash-Flow Discipline",
        "author": "after founder finance practice",
        "icon": "wallet",
        "tag": "Finance",
        "blurb": "Growth looks great on paper — but a cash crunch is 90 days away.",
        "intro": "Your P&L shows profit, yet the bank balance is falling. Revenue is up but so are receivables and inventory. Profit is an opinion; cash is a fact. You have one quarter to fix the runway.",
        "rounds": [
            {"id": 1, "situation": "Sales are booming but customers pay in 90 days while you pay suppliers in 30.",
             "question": "First lever?",
             "options": [
                 {"id": "a", "text": "Celebrate the sales growth and keep selling.", "score": 0,
                  "feedback": "Growth that widens the cash gap can bankrupt a profitable company."},
                 {"id": "b", "text": "Tighten receivables: deposits, milestones, faster collections.", "score": 3,
                  "feedback": "Cash conversion is the real game. Getting paid faster funds your growth."},
                 {"id": "c", "text": "Take a quick high-interest loan to bridge it.", "score": 1,
                  "feedback": "Sometimes necessary, but fix the working-capital cause, not just the symptom."}]},
            {"id": 2, "situation": "Inventory is piling up to 'never miss a sale'.",
             "question": "Your call?",
             "options": [
                 {"id": "a", "text": "Keep stocking; availability drives sales.", "score": 0,
                  "feedback": "Excess inventory is cash frozen on a shelf. It's a silent runway killer."},
                 {"id": "b", "text": "Right-size stock to real demand; free trapped cash.", "score": 3,
                  "feedback": "Inventory discipline releases cash without touching a single sale you'd actually make."},
                 {"id": "c", "text": "Ignore it; it's an accounting issue.", "score": 1,
                  "feedback": "It's very much a cash issue. Every unit is money you can't use."}]},
            {"id": 3, "situation": "A big-margin deal needs heavy upfront cash you don't have spare.",
             "question": "How do you decide?",
             "options": [
                 {"id": "a", "text": "Take it — the margin is too good to miss.", "score": 0,
                  "feedback": "A great margin you can't fund can still sink you. Model the cash, not just the profit."},
                 {"id": "b", "text": "Structure staged payments so cash-in leads cash-out.", "score": 3,
                  "feedback": "Deal design is finance. Make the customer's cash fund the work."},
                 {"id": "c", "text": "Decline all big deals for safety.", "score": 1,
                  "feedback": "Over-caution leaves growth on the table. Structure, don't just refuse."}]},
            {"id": 4, "situation": "You need a buffer for shocks.",
             "question": "What's your runway rule?",
             "options": [
                 {"id": "a", "text": "Hold a known months-of-runway cash reserve at all times.", "score": 3,
                  "feedback": "Knowing your runway to the day lets you lead from strength, not fear."},
                 {"id": "b", "text": "Keep just enough for this month.", "score": 0,
                  "feedback": "One bad month and you're negotiating from desperation."},
                 {"id": "c", "text": "Assume the line of credit will always be there.", "score": 1,
                  "feedback": "Credit lines shrink exactly when you need them most."}]},
            {"id": 5, "situation": "Costs need trimming without gutting the future.",
             "question": "Where do you cut?",
             "options": [
                 {"id": "a", "text": "Slash across the board equally, including growth engines.", "score": 0,
                  "feedback": "Blunt cuts damage the very things that create your recovery."},
                 {"id": "b", "text": "Protect revenue drivers; cut low-ROI spend surgically.", "score": 3,
                  "feedback": "Cut with a scalpel, not an axe. Defend what compounds."},
                 {"id": "c", "text": "Delay all cuts and hope revenue catches up.", "score": 1,
                  "feedback": "Hope isn't a plan when cash is draining."}]},
        ],
        "lessons": ["Profit is an opinion; cash is a fact — manage the cash conversion cycle.",
                    "Excess inventory and slow receivables are silent runway killers.",
                    "Design deals so cash-in leads cash-out; structure beats refusal.",
                    "Always know your runway to the day and hold a real reserve.",
                    "When trimming costs, use a scalpel — protect what compounds."],
    },
    {
        "slug": "supply-chain",
        "title": "The Bullwhip",
        "framework": "Supply-Chain & The Bullwhip Effect",
        "author": "after operations management practice",
        "icon": "truck",
        "tag": "Supply Chain",
        "blurb": "A small demand blip is about to whip into chaos across your supply chain.",
        "intro": "A minor uptick in end-customer demand is rippling upstream — and each tier is over-ordering to be safe. Left unmanaged, the bullwhip effect creates gluts, shortages and burned cash. Your job: dampen the whip.",
        "rounds": [
            {"id": 1, "situation": "Demand rose 10%. Your regional managers each order 30% more 'to be safe'.",
             "question": "Your response?",
             "options": [
                 {"id": "a", "text": "Approve it; better safe than out of stock.", "score": 0,
                  "feedback": "That over-reaction is the bullwhip starting. Small blips become huge upstream swings."},
                 {"id": "b", "text": "Order to actual demand signal, not to fear.", "score": 3,
                  "feedback": "Right. Ordering to real demand, not padded guesses, tames the whip at the source."},
                 {"id": "c", "text": "Freeze all orders until you understand it.", "score": 1,
                  "feedback": "Caution is fair, but a freeze can create the very shortage you fear."}]},
            {"id": 2, "situation": "Each tier hoards its own forecast in a spreadsheet.",
             "question": "Structural fix?",
             "options": [
                 {"id": "a", "text": "Share real demand data across all tiers.", "score": 3,
                  "feedback": "Information sharing is the number-one bullwhip cure. Everyone plans off the same truth."},
                 {"id": "b", "text": "Let each tier keep guessing independently.", "score": 0,
                  "feedback": "Independent guesses amplify error at every step."},
                 {"id": "c", "text": "Add more safety stock everywhere.", "score": 1,
                  "feedback": "That treats the symptom and freezes even more cash."}]},
            {"id": 3, "situation": "Bulk-order discounts tempt managers to buy in huge, lumpy batches.",
             "question": "What do you do?",
             "options": [
                 {"id": "a", "text": "Chase every bulk discount for unit savings.", "score": 0,
                  "feedback": "Lumpy ordering is a classic bullwhip driver. The 'savings' hide inventory and swing costs."},
                 {"id": "b", "text": "Move to smaller, more frequent orders.", "score": 3,
                  "feedback": "Smoother, smaller orders flatten the swings and free cash."},
                 {"id": "c", "text": "Order bulk only sometimes, at random.", "score": 1,
                  "feedback": "Randomness adds noise the whole chain must absorb."}]},
            {"id": 4, "situation": "A key supplier has a 6-week lead time and it's hurting responsiveness.",
             "question": "Best lever?",
             "options": [
                 {"id": "a", "text": "Work to shorten lead times and qualify a backup source.", "score": 3,
                  "feedback": "Shorter, more reliable lead times shrink the forecast horizon — and the whip."},
                 {"id": "b", "text": "Just carry six weeks of extra stock forever.", "score": 1,
                  "feedback": "It hides the problem at a permanent cash cost."},
                 {"id": "c", "text": "Do nothing; lead time is fixed.", "score": 0,
                  "feedback": "Lead time is usually more negotiable than teams assume."}]},
            {"id": 5, "situation": "Promotions cause wild demand spikes then troughs.",
             "question": "How do you plan promotions?",
             "options": [
                 {"id": "a", "text": "Coordinate promotions with supply and share the plan upstream.", "score": 3,
                  "feedback": "Aligning demand-shaping with supply planning prevents self-inflicted whips."},
                 {"id": "b", "text": "Let marketing run promos without telling operations.", "score": 0,
                  "feedback": "That's a self-inflicted bullwhip — the worst kind because it's avoidable."},
                 {"id": "c", "text": "Stop all promotions entirely.", "score": 1,
                  "feedback": "You lose a growth lever instead of simply coordinating it."}]},
        ],
        "lessons": ["Order to the real demand signal, not to padded fear — that's where the whip starts.",
                    "Sharing real demand data across tiers is the single biggest bullwhip cure.",
                    "Smaller, more frequent orders beat lumpy bulk buying.",
                    "Shorter, reliable lead times shrink the forecast horizon and the swings.",
                    "Coordinate demand-shaping (promotions) with supply to avoid self-inflicted chaos."],
    },
]

GAMES_BY_SLUG = {g["slug"]: g for g in GAMES}


def game_card(g: dict) -> dict:
    """Public list view — no answers/scores."""
    return {"slug": g["slug"], "title": g["title"], "framework": g["framework"],
            "author": g["author"], "icon": g["icon"], "tag": g["tag"],
            "blurb": g["blurb"], "rounds": len(g["rounds"]),
            "max_score": sum(max(o["score"] for o in r["options"]) for r in g["rounds"])}


def game_play(g: dict) -> dict:
    """Full game payload for playing (options carry score + feedback)."""
    return {**game_card(g), "intro": g["intro"], "lessons": g["lessons"],
            "rounds": g["rounds"]}


def debrief(g: dict, score: int) -> dict:
    """SK-voice debrief keyed to the player's score band."""
    max_score = sum(max(o["score"] for o in r["options"]) for r in g["rounds"])
    pct = (score / max_score) if max_score else 0
    if pct >= 0.8:
        band, title = "high", "Commanding play"
        note = ("You led like a seasoned operator — reading the situation before reacting, owning the "
                "hard calls, and choosing the disciplined move over the dramatic one. This is exactly the "
                "instinct I try to build in the CXOs I coach. Now make it a habit, not a one-off.")
    elif pct >= 0.5:
        band, title = "mid", "Solid, with sharp edges to grind"
        note = ("A capable performance with a few costly reflexes. You have the right instincts; the gap is "
                "consistency under pressure. Re-read the feedback on the choices you got wrong — that's where "
                "the real leverage is. Good leaders are simply people who keep closing that gap.")
    else:
        band, title = "low", "The lesson is the reward"
        note = ("This round cost you — and that's the point of a simulation: to spend the tuition here, not in "
                "the real boardroom. Go back through the feedback on each decision. The frameworks aren't "
                "theory; they're pattern recognition you can build. Run it again and watch your score climb.")
    return {"band": band, "title": title, "note": note, "score": score, "max_score": max_score,
            "lessons": g["lessons"], "framework": g["framework"]}
