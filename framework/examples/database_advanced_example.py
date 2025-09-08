# ==============================================================================
# examples/database_advanced_example.py - Esempio avanzato database
# ==============================================================================

"""
Esempio avanzato per gestione database con:
- Migrazioni
- Modelli custom
- Query complesse
- Transazioni
- Gestione errori
"""

import asyncio
from framework import ModularFramework
from framework.database.models import Base, Configuration, LogEntry
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import random


# Modelli custom per l'esempio
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relazione con posts
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    published = Column(Boolean, default=False)

    # Relazione con utente
    author = relationship("User", back_populates="posts")


async def database_advanced_example():
    """Esempio avanzato database"""

    print("🗃️ === DATABASE ADVANCED EXAMPLE ===\n")

    # Inizializza framework
    fw = ModularFramework()
    fw.setup_database()

    # Crea tabelle custom
    Base.metadata.create_all(bind=fw.db.engine)
    print("✅ Tabelle create")

    try:
        # =======================================================================
        # 1. OPERAZIONI CRUD AVANZATE
        # =======================================================================
        print("\n📝 1. Operazioni CRUD...")

        with fw.db.get_session() as session:
            # Crea utenti
            users_data = [
                {"username": "alice", "email": "alice@example.com"},
                {"username": "bob", "email": "bob@example.com"},
                {"username": "carol", "email": "carol@example.com"}
            ]

            users = []
            for user_data in users_data:
                # Controlla se esiste già
                existing = session.query(User).filter(User.username == user_data["username"]).first()
                if not existing:
                    user = User(**user_data)
                    session.add(user)
                    users.append(user)

            session.commit()
            print(f"   ✅ Creati {len(users)} utenti")

            # Ottieni utenti per i post
            all_users = session.query(User).all()

            # Crea post
            posts_data = [
                {"title": "Primo Post", "content": "Contenuto del primo post..."},
                {"title": "Tutorial Python", "content": "Come usare Python per..."},
                {"title": "Database Design", "content": "Principi di design database..."},
                {"title": "API REST", "content": "Come progettare API REST..."},
                {"title": "Microservizi", "content": "Architettura a microservizi..."}
            ]

            posts = []
            for post_data in posts_data:
                # Assegna autore casuale
                author = random.choice(all_users)
                post = Post(
                    title=post_data["title"],
                    content=post_data["content"],
                    author_id=author.id,
                    published=random.choice([True, False])
                )
                session.add(post)
                posts.append(post)

            session.commit()
            print(f"   ✅ Creati {len(posts)} post")

        # =======================================================================
        # 2. QUERY COMPLESSE
        # =======================================================================
        print("\n🔍 2. Query Complesse...")

        with fw.db.get_session() as session:
            # Query con JOIN
            published_posts = session.query(Post).join(User).filter(
                Post.published == True,
                User.is_active == True
            ).all()

            print(f"   📊 Post pubblicati: {len(published_posts)}")

            # Raggruppa per autore
            from sqlalchemy import func
            posts_per_author = session.query(
                User.username,
                func.count(Post.id).label('post_count')
            ).join(Post).group_by(User.username).all()

            print("   👥 Post per autore:")
            for username, count in posts_per_author:
                print(f"      {username}: {count} post")

            # Query con subquery
            active_authors = session.query(User).filter(
                User.id.in_(
                    session.query(Post.author_id).filter(Post.published == True)
                )
            ).all()

            print(f"   ✍️  Autori attivi: {len(active_authors)}")

        # =======================================================================
        # 3. TRANSAZIONI E GESTIONE ERRORI
        # =======================================================================
        print("\n🔄 3. Transazioni...")

        # Transazione con successo
        try:
            with fw.db.get_session() as session:
                # Crea nuovo utente e post in una transazione
                new_user = User(
                    username="david",
                    email="david@example.com"
                )
                session.add(new_user)
                session.flush()  # Per ottenere l'ID

                new_post = Post(
                    title="Post in Transazione",
                    content="Questo post è stato creato in una transazione",
                    author_id=new_user.id,
                    published=True
                )
                session.add(new_post)

                # Commit automatico con context manager
                print("   ✅ Transazione completata con successo")

        except Exception as e:
            print(f"   ❌ Errore transazione: {e}")

        # Transazione con rollback simulato
        try:
            with fw.db.get_session() as session:
                # Crea utente
                test_user = User(
                    username="test_rollback",
                    email="test@example.com"
                )
                session.add(test_user)
                session.flush()

                # Simula errore (email duplicata)
                duplicate_user = User(
                    username="test_rollback2",
                    email="test@example.com"  # Email duplicata
                )
                session.add(duplicate_user)
                # Il commit solleverà un'eccezione

        except Exception as e:
            print(f"   ✅ Rollback automatico per errore: {type(e).__name__}")

        # =======================================================================
        # 4. PERFORMANCE E OTTIMIZZAZIONI
        # =======================================================================
        print("\n🚀 4. Performance...")

        # Eager loading
        with fw.db.get_session() as session:
            from sqlalchemy.orm import joinedload

            # Carica utenti con tutti i loro post in una query
            users_with_posts = session.query(User).options(
                joinedload(User.posts)
            ).all()

            print(f"   📚 Utenti con post (eager loading): {len(users_with_posts)}")
            for user in users_with_posts:
                print(f"      {user.username}: {len(user.posts)} post")

        # Bulk operations
        with fw.db.get_session() as session:
            # Aggiorna tutti i post di un autore
            updated = session.query(Post).filter(
                Post.author_id == 1
            ).update({Post.published: True})

            print(f"   🔄 Aggiornati {updated} post in bulk")

        # =======================================================================
        # 5. QUERY RAW SQL
        # =======================================================================
        print("\n🔧 5. Query SQL Raw...")

        # Query complessa con SQL raw
        complex_query = """
        SELECT 
            u.username,
            COUNT(p.id) as total_posts,
            COUNT(CASE WHEN p.published = 1 THEN 1 END) as published_posts,
            MAX(p.created_at) as last_post_date
        FROM users u
        LEFT JOIN posts p ON u.id = p.author_id
        WHERE u.is_active = 1
        GROUP BY u.id, u.username
        ORDER BY total_posts DESC
        """

        results = fw.db.execute_query(complex_query)
        print("   📊 Statistiche autori:")
        for row in results:
            print(f"      {row['username']}: {row['total_posts']} total, {row['published_posts']} pubblicati")

        # =======================================================================
        # 6. BACKUP E RESTORE (SQLite)
        # =======================================================================
        if fw.config.database.provider == 'sqlite':
            print("\n💾 6. Backup SQLite...")

            import shutil
            from pathlib import Path

            # Backup
            source_db = Path(fw.config.database.sqlite_path)
            backup_db = source_db.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            shutil.copy2(source_db, backup_db)
            print(f"   ✅ Backup creato: {backup_db}")

            # Verifica backup
            if backup_db.exists():
                backup_size = backup_db.stat().st_size
                original_size = source_db.stat().st_size
                print(f"   📊 Dimensione originale: {original_size} bytes")
                print(f"   📊 Dimensione backup: {backup_size} bytes")

        print("\n🎉 === ESEMPIO DATABASE COMPLETATO ===")

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(database_advanced_example())