from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import io
import os

app = Flask(__name__)
CORS(app)

# Configuration pour Render
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

class ProjectionDemographique:
    def __init__(self):
        self.resultats = {}
    
    def calculer_coefficients(self, m0, m1, m2):
        c = m0
        b = (4 * m1 - m2 - 3 * m0) / 4
        a = (m2 - 2 * m1 + m0) / 8
        return a, b, c
    
    def calculer_population(self, a, b, c, t):
        return a * (t ** 2) + b * t + c
    
    def effectuer_projection(self, nom_ville, population_2016, population_2018, population_2020):
        a, b, c = self.calculer_coefficients(population_2016, population_2018, population_2020)
        
        projections = {}
        projections[2016] = population_2016
        projections[2018] = population_2018
        projections[2020] = population_2020
        projections[2023] = self.calculer_population(a, b, c, 7)
        projections[2024] = self.calculer_population(a, b, c, 8)
        projections[2025] = self.calculer_population(a, b, c, 9)
        projections[2026] = self.calculer_population(a, b, c, 10)
        
        resultat_ville = {
            'coefficients': {'a': a, 'b': b, 'c': c},
            'projections': projections
        }
        
        self.resultats[nom_ville] = resultat_ville
        return resultat_ville
    
    def exporter_excel(self):
        if not self.resultats:
            return None
        
        donnees_export = []
        for ville, data in self.resultats.items():
            ligne = {'Ville': ville}
            ligne.update(data['projections'])
            ligne.update({
                'Coefficient a': data['coefficients']['a'],
                'Coefficient b': data['coefficients']['b'],
                'Coefficient c': data['coefficients']['c']
            })
            donnees_export.append(ligne)
        
        df = pd.DataFrame(donnees_export)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Projections', index=False)
        output.seek(0)
        return output

# Instance globale du modèle
modele = ProjectionDemographique()

@app.route('/')
def home():
    return jsonify({
        "message": "API de Projection Démographique - Lab_math_RMT et CIE 2025",
        "status": "online",
        "endpoints": {
            "ajouter_ville": "/api/ajouter_ville (POST)",
            "get_villes": "/api/get_villes (GET)",
            "export_excel": "/api/export_excel (GET)",
            "reinitialiser": "/api/reinitialiser (POST)",
            "charger_exemples": "/api/charger_exemples (POST)"
        }
    })

@app.route('/api/ajouter_ville', methods=['POST'])
def ajouter_ville():
    try:
        data = request.get_json()
        
        nom_ville = data.get('nom_ville')
        population_2016 = float(data.get('population_2016'))
        population_2018 = float(data.get('population_2018'))
        population_2020 = float(data.get('population_2020'))
        
        if not nom_ville or population_2016 < 0 or population_2018 < 0 or population_2020 < 0:
            return jsonify({'erreur': 'Données invalides'}), 400
        
        resultats = modele.effectuer_projection(nom_ville, population_2016, population_2018, population_2020)
        
        return jsonify({
            'success': True,
            'ville': nom_ville,
            'resultats': resultats
        })
        
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500

@app.route('/api/get_villes', methods=['GET'])
def get_villes():
    return jsonify(modele.resultats)

@app.route('/api/export_excel', methods=['GET'])
def export_excel():
    try:
        excel_file = modele.exporter_excel()
        if excel_file is None:
            return jsonify({'erreur': 'Aucune donnée à exporter'}), 400
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='projections_demographiques.xlsx'
        )
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500

@app.route('/api/reinitialiser', methods=['POST'])
def reinitialiser():
    try:
        modele.resultats = {}
        return jsonify({'success': True, 'message': 'Données réinitialisées'})
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500

@app.route('/api/charger_exemples', methods=['POST'])
def charger_exemples():
    try:
        donnees_villes = {
            "NGAOUNDÉRÉ I": [109423, 115772, 122282],
            "NGAOUNDÉRÉ II": [118764, 125655, 132721],
            "NGAOUNDÉRÉ III": [24501, 25923, 27380],
            "YAOUNDE 1": [429252, 461134, 494353],
            "YAOUNDE 2": [361606, 388463, 416448],
        }
        
        for ville, populations in donnees_villes.items():
            modele.effectuer_projection(ville, populations[0], populations[1], populations[2])
        
        return jsonify({
            'success': True, 
            'message': f'{len(donnees_villes)} villes chargées avec succès',
            'villes_ajoutees': list(donnees_villes.keys())
        })
        
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)