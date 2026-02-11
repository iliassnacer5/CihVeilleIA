import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from app.dashboard.ui_utils import apply_cih_theme, cih_metric, render_logo
from app.search.semantic_search import SemanticSearchEngine, SearchFilters
from app.rag.pipeline import RagPipeline
from app.storage.mongo_store import MongoEnrichedDocumentStore

# Mock data for statistics (if database is empty)
MOCK_TOPICS = {
    "Innovation et Fintech": 35,
    "Réglementation bancaire": 28,
    "Cybersécurité": 22,
    "Intelligence artificielle": 45,
    "Risque de crédit": 15
}

def load_data():
    """Charge les données réelles pour les statistiques si possible."""
    try:
        store = MongoEnrichedDocumentStore()
        # On récupère les documents récents
        docs = list(store.collection.find({}, {"topics": 1, "lang": 1, "created_at": 1}).limit(500))
        if not docs:
            return None
        return pd.DataFrame(docs)
    except Exception:
        return None

def render_statistics():
    st.header("📊 Statistiques de Veille")
    
    df = load_data()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_docs = len(df) if df is not None else 145
        cih_metric("Documents Indexés", total_docs, "+12")
    with col2:
        num_sources = 12 # Placeholder
        cih_metric("Sources Actives", num_sources)
    with col3:
        cih_metric("Alertes 24h", 8)
    with col4:
        cih_metric("Mise à jour", "Il y a 2h")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Répartition par Thématique")
        if df is not None and "topics" in df.columns:
            # Explosion des listes de topics pour le comptage
            all_topics = df.explode("topics")["topics"].value_counts().reset_index()
            all_topics.columns = ["Topic", "Count"]
            fig = px.bar(all_topics.head(10), x="Count", y="Topic", orientation='h', 
                         color_discrete_sequence=['#004687'])
        else:
            fig = px.bar(x=list(MOCK_TOPICS.values()), y=list(MOCK_TOPICS.keys()), orientation='h',
                         labels={'x': 'Volume', 'y': 'Thématique'},
                         color_discrete_sequence=['#004687'])
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Volume par Langue")
        if df is not None and "lang" in df.columns:
            lang_counts = df["lang"].value_counts().reset_index()
            lang_counts.columns = ["Langue", "Count"]
            fig = px.pie(lang_counts, values='Count', names='Langue', hole=0.4,
                         color_discrete_sequence=['#004687', '#FF8200', '#A0A0A0'])
        else:
            fig = px.pie(values=[60, 30, 10], names=['English', 'French', 'Arabic'], hole=0.4,
                         color_discrete_sequence=['#004687', '#FF8200', '#A0A0A0'])
        st.plotly_chart(fig, use_container_width=True)

def render_search():
    st.header("🔍 Recherche Sémantique")
    
    if "search_engine" not in st.session_state:
        st.session_state.search_engine = SemanticSearchEngine()
    
    engine = st.session_state.search_engine

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Saisissez votre recherche (ex: impact de l'IA sur le risque de crédit)", 
                             placeholder="Concepts, phrases ou mots-clés...")
    with col2:
        search_type = st.selectbox("Méthode", ["Sémantique (FAISS)", "Mots-clés (Mongo)", "Hybride"])

    with st.expander("Filtres avancés"):
        c1, c2, c3 = st.columns(3)
        with c1:
            lang = st.multiselect("Langue", ["en", "fr", "ar"])
        with c2:
            date_range = st.date_input("Période", [datetime.now() - timedelta(days=30), datetime.now()])
        with c3:
            min_score = st.slider("Score minimum", 0.0, 1.0, 0.3)

    if st.button("Lancer la recherche") and query:
        with st.spinner("Analyse du sens et recherche des documents..."):
            filters = SearchFilters(
                lang=lang[0] if lang else None,
                start_date=datetime.combine(date_range[0], datetime.min.time()) if len(date_range) > 0 else None,
                end_date=datetime.combine(date_range[1], datetime.max.time()) if len(date_range) > 1 else None
            )
            
            if search_type == "Sémantique (FAISS)":
                results = engine.vector_search(query, filters=filters)
            elif search_type == "Mots-clés (Mongo)":
                results = engine.keyword_search(query, filters=filters)
            else:
                results = engine.hybrid_search(query, filters=filters)

        if not results:
            st.info("Aucun résultat ne correspond à votre recherche.")
        else:
            st.success(f"{len(results)} résultats trouvés.")
            for res in results:
                with st.container():
                    st.markdown(f"### [{res.title}]({res.url or '#'})")
                    st.markdown(f"**Source:** {res.source_id} | **Score:** {res.score:.2f} | **Type:** {res.score_type}")
                    st.write(res.text_snippet)
                    if res.topics:
                        st.caption(f"Tags: {', '.join(res.topics)}")
                    st.divider()

def render_chatbot():
    st.header("🤖 Assistant Intelligence RAG")
    st.info("Posez-moi une question sur le contenu de la veille. J'utilise les documents indexés pour vous répondre précisément.")

    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = RagPipeline()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Votre question (ex: Quelles sont les nouvelles directives de Bank Al-Maghrib ?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours..."):
                result = st.session_state.rag_pipeline.answer_question(prompt)
                response = result.answer
                st.markdown(response)
                
                if result.context:
                    with st.expander("Sources consultées"):
                        for i, ctx in enumerate(result.context[:3]):
                            st.caption(f"Source {i+1}: {ctx[:200]}...")

        st.session_state.messages.append({"role": "assistant", "content": response})

def render_alerts():
    st.header("🔔 Dernières Alertes")
    
    try:
        store = MongoEnrichedDocumentStore()
        alerts = list(store.collection.find().sort("created_at", -1).limit(10))
    except Exception:
        alerts = []

    if not alerts:
        st.warning("Aucune alerte récente. Le système est en attente de nouveaux flux.")
        return

    for alert in alerts:
        with st.expander(f"{alert.get('title', 'Sans titre')} - {alert.get('created_at', datetime.now()).strftime('%H:%M')}"):
            st.markdown(f"**Source:** {alert.get('source_id', 'Inconnue')}")
            st.write(alert.get('summary', alert.get('text', '')[:300] + "..."))
            if st.button("Voir les détails", key=str(alert['_id'])):
                st.json(alert)

def render_audit_trail():
    st.header("📋 Registre d'Audit & Conformité")
    st.info("Visualisation des événements de sécurité, du scraping et de la traçabilité IA (Auditable par le régulateur).")

    try:
        from pymongo import MongoClient
        from app.config.settings import settings
        client = MongoClient(settings.mongodb_uri)
        db = client["cih_audit"]
        logs = list(db["audit_trail"].find().sort("timestamp", -1).limit(50))
    except Exception as e:
        st.error(f"Impossible de charger les logs d'audit : {e}")
        return

    if not logs:
        st.warning("Aucun log d'audit disponible.")
        return

    # Filter by event type
    event_types = ["Tous"] + sorted(list(set(l["event_type"] for l in logs)))
    selected_type = st.selectbox("Filtrer par type d'événement", event_types)

    for log in logs:
        if selected_type != "Tous" and log["event_type"] != selected_type:
            continue
            
        color = "🔴" if log["event_type"] == "SECURITY_ALERT" else "🔵"
        with st.expander(f"{color} {log['timestamp'].strftime('%H:%M:%S')} - {log['event_type']} : {log['action']}"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Status:** {log['status']}")
                st.write(f"**Utilisateur:** {log['user_id']}")
            with c2:
                st.write("**Détails techniques:**")
                st.json(log["details"])

def main():
    st.set_page_config(
        page_title="CIH Veille IA - Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_cih_theme()
    render_logo()

    menu = ["Tableau de Bord", "Recherche Sémantique", "Assistant RAG", "Dernières Alertes", "Audit Trail"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Tableau de Bord":
        render_statistics()
    elif choice == "Recherche Sémantique":
        render_search()
    elif choice == "Assistant RAG":
        render_chatbot()
    elif choice == "Dernières Alertes":
        render_alerts()
    elif choice == "Audit Trail":
        render_audit_trail()

if __name__ == "__main__":
    main()
