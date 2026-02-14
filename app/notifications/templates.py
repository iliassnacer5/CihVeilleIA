import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_alert_email_template(data: Dict[str, Any]) -> str:
    """Génère un template HTML professionnel aux couleurs de CIH Bank."""
    
    title = data.get("title", "Nouvelle Information Réglementaire")
    source = data.get("source", "Source Non Spécifiée")
    date = data.get("date", datetime.now().strftime("%d/%m/%Y"))
    summary = data.get("summary", "Aucun résumé disponible.")
    score = data.get("score", 0.0)
    url = data.get("url", "#")
    priority = data.get("priority", "NORMAL").upper()
    
    # Couleurs CIH Bank
    color_primary = "#c41230" # Rouge CIH
    color_secondary = "#004a99" # Bleu CIH
    color_accent = "#d4af37" # Or/Bronze
    
    priority_color = {
        "CRITICAL": "#c41230",
        "IMPORTANT": "#e67e22",
        "NORMAL": "#3498db"
    }.get(priority, "#3498db")

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 650px; margin: 20px auto; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden; }}
            .header {{ background-color: {color_primary}; color: white; padding: 25px; text-align: center; }}
            .content {{ padding: 30px; background-color: #ffffff; }}
            .footer {{ background-color: #f8f9fa; color: #6c757d; padding: 20px; text-align: center; font-size: 12px; border-top: 1px solid #eee; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 15px; }}
            .badge-priority {{ background-color: {priority_color}; color: white; }}
            .document-title {{ color: {color_secondary}; font-size: 22px; margin-top: 0; margin-bottom: 10px; border-bottom: 2px solid {color_accent}; padding-bottom: 8px; }}
            .metadata {{ background-color: #f1f4f8; padding: 15px; border-radius: 4px; margin: 20px 0; font-size: 14px; border-left: 4px solid {color_secondary}; }}
            .summary-box {{ margin-top: 25px; }}
            .btn {{ display: inline-block; background-color: {color_secondary}; color: white !important; padding: 12px 25px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; }}
            .score-indicator {{ font-weight: bold; color: {color_primary if score > 0.9 else color_secondary}; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; letter-spacing: 1px;">CIH BANK - VEILLE IA</h1>
            </div>
            <div class="content">
                <div class="badge badge-priority">{priority}</div>
                <h2 class="document-title">{title}</h2>
                
                <div class="metadata">
                    <p style="margin: 5px 0;"><strong>Source :</strong> {source}</p>
                    <p style="margin: 5px 0;"><strong>Date de Publication :</strong> {date}</p>
                    <p style="margin: 5px 0;"><strong>Score de Pertinence :</strong> <span class="score-indicator">{score:.2f}</span></p>
                </div>
                
                <div class="summary-box">
                    <h3 style="color: {color_secondary}; border-bottom: 1px solid #eee; padding-bottom: 5px;">Résumé Analytique</h3>
                    <p>{summary}</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{url}" class="btn">VOIR LE DOCUMENT COMPLET</a>
                </div>
            </div>
            <div class="footer">
                <p>Ce message est une alerte automatique généré par le système CIH-Veille-IA.</p>
                <p>Confidentiel - Usage Interne Uniquement</p>
                <p>&copy; 2026 CIH Bank - Direction de la Conformité</p>
            </div>
        </div>
    </body>
    </html>
    """
