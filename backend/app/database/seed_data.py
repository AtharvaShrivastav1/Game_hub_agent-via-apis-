from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.game import Game
from app.models.cart import CartItem
from app.models.purchase import Purchase
from app.models.library import UserGameLibrary

SAMPLE_GAMES: List[Dict[str, Any]] = [
    {
        "title": "Cyberstrike: Neon Protocol",
        "description": "A dark cyberpunk action RPG set in a sprawling dystopian megacity. Augment your body with neural hardware, hack corporate grids, and engage in high-octane tactical combat against rogue syndicates.",
        "genre": "RPG",
        "price": 2499.00,
        "rating": 4.8,
        "duration_hours": 65.0,
        "developer": "GhostByte Interactive",
        "release_date": "2024-03-15",
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Chronicles of Eldoria",
        "description": "An expansive open-world fantasy RPG with branching moral choices, dragon raids, and deep arcane magiccraft. Explore ancient ruins across three vast kingdoms with over 100 hours of questing.",
        "genre": "RPG",
        "price": 1499.00,
        "rating": 4.9,
        "duration_hours": 95.0,
        "developer": "Mythic Realm Studios",
        "release_date": "2023-11-10",
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Valkyrie Ascendant",
        "description": "A punishing souls-like action spectacle inspired by Norse mythology. Master parrying, stance-breaking, and runic weaponry as you duel fallen gods amidst the twilight of Valhalla.",
        "genre": "Action",
        "price": 1899.00,
        "rating": 4.7,
        "duration_hours": 42.0,
        "developer": "Ironclad Games",
        "release_date": "2024-01-20",
        "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Hollow Depths: Requiem",
        "description": "An atmospheric 2D metroidvania set in an interconnected subterranean kingdom. Uncover forgotten lore, discover fluid acrobatics, and face eerie insectoid monstrosities.",
        "genre": "Indie",
        "price": 699.00,
        "rating": 4.9,
        "duration_hours": 28.0,
        "developer": "Moonlit Weave",
        "release_date": "2023-08-04",
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Stellar Dominion: Galactic War",
        "description": "A grand 4X space strategy simulator. Design fleets, manage orbital planetary colonies, negotiate fragile interstellar treaties, and wage galaxy-spanning warfare in real time.",
        "genre": "Strategy",
        "price": 1799.00,
        "rating": 4.6,
        "duration_hours": 120.0,
        "developer": "Nova Forge Games",
        "release_date": "2023-09-12",
        "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Dead Silence: Blackwood Manor",
        "description": "A bone-chilling psychological survival horror game with dynamic AI stalkers. Armed only with a malfunctioning camcorder, survive a nocturnal nightmare in an abandoned Victorian sanatorium.",
        "genre": "Horror",
        "price": 899.00,
        "rating": 4.5,
        "duration_hours": 12.0,
        "developer": "Crimson Door Studio",
        "release_date": "2023-10-31",
        "image_url": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Apex Velocity: Horizon Drift",
        "description": "A hyper-realistic open-world street racing game featuring dynamic rain physics, over 200 customizable supercars, and nocturnal drift battles across neon-lit mountain passes.",
        "genre": "Racing",
        "price": 1299.00,
        "rating": 4.4,
        "duration_hours": 35.0,
        "developer": "Torque Shift Labs",
        "release_date": "2024-02-14",
        "image_url": "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Quantum Enigma",
        "description": "A mind-bending first-person puzzle game manipulating temporal paradoxes and anti-gravity fields to escape an anomalous research facility hidden beneath the Antarctic ice.",
        "genre": "Puzzle",
        "price": 799.00,
        "rating": 4.7,
        "duration_hours": 15.0,
        "developer": "Singularity Creations",
        "release_date": "2023-05-18",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Meadowvale: Cozy Homestead",
        "description": "A charming and peaceful farming life-sim. Cultivate organic heirloom crops, befriend eccentric village artisans, forage enchanted mushrooms, and restore an ancestral farmstead at your own pace.",
        "genre": "Simulation",
        "price": 599.00,
        "rating": 4.8,
        "duration_hours": 70.0,
        "developer": "Sunny Acre Studios",
        "release_date": "2023-04-10",
        "image_url": "https://images.unsplash.com/photo-1500651230702-0e2d8a49d4ad?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Shadow Blade: Shinobi's Oath",
        "description": "A razor-sharp stealth action adventure set in Sengoku-era feudal Japan. Utilize grappling hooks, smoke bombs, and katana assassination techniques under the cover of moonlight.",
        "genre": "Action",
        "price": 1599.00,
        "rating": 4.6,
        "duration_hours": 24.0,
        "developer": "Kurogane Works",
        "release_date": "2023-12-05",
        "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Rogue Galaxy: Starfarer",
        "description": "A deckbuilding rogue-lite space adventure. Pilot unique starships, assemble synergistic energy weapon combos, and chart jump routes across hostile alien sectors.",
        "genre": "Indie",
        "price": 499.00,
        "rating": 4.8,
        "duration_hours": 45.0,
        "developer": "Pixel Orbit",
        "release_date": "2023-07-22",
        "image_url": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Tactics & Treason: King's Fall",
        "description": "A grid-based turn-based tactical RPG with deep class customization and dark political intrigue. Lead a rebellion of outcasts against a corrupt feudal empire.",
        "genre": "Strategy",
        "price": 1199.00,
        "rating": 4.5,
        "duration_hours": 50.0,
        "developer": "Crown & Dagger",
        "release_date": "2024-04-02",
        "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Riftwalker: Dimensional Odyssey",
        "description": "An action RPG featuring fluid dimension-shifting traversal. Dash across fractured realities, combine elemental spells, and uncover the mystery of the collapsing cosmos.",
        "genre": "RPG",
        "price": 1999.00,
        "rating": 4.6,
        "duration_hours": 38.0,
        "developer": "Prism Forge",
        "release_date": "2024-05-11",
        "image_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Subnautica Deep: Trench Odyssey",
        "description": "Descend into an alien oceanic trench. Craft submersible vessels, avoid colossal bioluminescent leviathans, and build thermal research outposts in total darkness.",
        "genre": "Adventure",
        "price": 1399.00,
        "rating": 4.7,
        "duration_hours": 32.0,
        "developer": "Abyssal Tech",
        "release_date": "2023-06-30",
        "image_url": "https://images.unsplash.com/photo-1682687220063-4742bd7fd538?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Frostfall: Colony Survival",
        "description": "A gripping post-apocalyptic survival city builder set in a perpetual volcanic winter. Manage thermal steam generators, allocate rations, and make heartbreaking executive decisions.",
        "genre": "Simulation",
        "price": 1499.00,
        "rating": 4.7,
        "duration_hours": 40.0,
        "developer": "Blizzard Peak",
        "release_date": "2023-03-29",
        "image_url": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Midnight Manor: Escape",
        "description": "An intense escape-room horror puzzle game. Decipher Victorian clockwork mechanisms, uncover coded diaries, and evade a relentless supernatural entity before dawn.",
        "genre": "Horror",
        "price": 799.00,
        "rating": 4.3,
        "duration_hours": 10.0,
        "developer": "GraveLight Interactive",
        "release_date": "2023-10-13",
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Gridiron Heroes: Blitz 25",
        "description": "The definitive next-generation football simulation with physics-based tackling, dynamic stadium weather, and an in-depth franchise manager mode.",
        "genre": "Simulation",
        "price": 2999.00,
        "rating": 4.1,
        "duration_hours": 80.0,
        "developer": "Polygon Sports",
        "release_date": "2024-08-20",
        "image_url": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "Pixel Dungeon: Endless Descent",
        "description": "A retro-inspired roguelike dungeon crawler with procedural labyrinths, 150+ magical artifacts, permadeath, and pixel-art boss encounters.",
        "genre": "Indie",
        "price": 399.00,
        "rating": 4.8,
        "duration_hours": 60.0,
        "developer": "Chiptune Games",
        "release_date": "2023-01-15",
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=800&q=80",
    }
]

def reset_and_seed_database(db: Session, reset_user_data: bool = True):
    """
    Ensures games catalog is populated and resets user library, cart, purchases,
    and wallet balance to initial state (fresh state with no games in library).
    """
    # 1. Ensure/Seed Games
    for g_data in SAMPLE_GAMES:
        existing = db.query(Game).filter(Game.title == g_data["title"]).first()
        if not existing:
            game = Game(**g_data)
            db.add(game)
    db.commit()

    # 2. Ensure User Alex Mercer (id=1)
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            name="Alex Mercer",
            email="alex.mercer@gamehub.io",
            wallet_balance=3500.00
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif reset_user_data:
        user.wallet_balance = 3500.00
        db.commit()

    # 3. Clean user library, cart, and purchases if reset is requested
    if reset_user_data:
        db.query(UserGameLibrary).filter(UserGameLibrary.user_id == 1).delete(synchronize_session=False)
        db.query(CartItem).filter(CartItem.user_id == 1).delete(synchronize_session=False)
        db.query(Purchase).filter(Purchase.user_id == 1).delete(synchronize_session=False)
        db.commit()
