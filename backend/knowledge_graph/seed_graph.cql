// AI-Powered Grain Spoilage Prevention System
// Neo4j Climate-to-Spoilage Knowledge Graph Seed Script (Cypher)

// Clear existing domain graph if necessary
MATCH (n) DETACH DELETE n;

// 1. Create Regional Agro-Climatic Nodes
CREATE (r1:Region {name: 'Haryana', zone: 'Trans-Gangetic Plains', state: 'Haryana', mandi_cluster: 'Gurugram / Sohna / Karnal'})
CREATE (r2:Region {name: 'Punjab', zone: 'Trans-Gangetic Plains', state: 'Punjab', mandi_cluster: 'Ludhiana / Khanna'})
CREATE (r3:Region {name: 'Western UP', zone: 'Upper Gangetic Plains', state: 'Uttar Pradesh', mandi_cluster: 'Meerut / Hapur'});

// 2. Create Climate Event Nodes
CREATE (c1:ClimateEvent {
    name: 'Pre-Monsoon Humidity Surge',
    min_temp: 27.0,
    min_rh: 72.0,
    historical_incidence_score: 0.88,
    season: 'June - July',
    description: 'Rapid moisture influx before heavy rainfall leads to interstitial humidity spikes.'
})
CREATE (c2:ClimateEvent {
    name: 'Unseasonal Post-Harvest Rainfall',
    min_temp: 22.0,
    min_rh: 80.0,
    historical_incidence_score: 0.79,
    season: 'March - April / October',
    description: 'Western disturbances causing sudden dampening and wet grain intake.'
})
CREATE (c3:ClimateEvent {
    name: 'Peak Summer Thermal Heatwave',
    min_temp: 36.0,
    min_rh: 35.0,
    historical_incidence_score: 0.65,
    season: 'May - June',
    description: 'Elevated ambient heat accelerates insect metabolic reproduction and thermal convection.'
})
CREATE (c4:ClimateEvent {
    name: 'Winter Fog & High Nighttime RH',
    min_temp: 8.0,
    min_rh: 85.0,
    historical_incidence_score: 0.58,
    season: 'December - January',
    description: 'Severe temperature differentials between warm grain core and freezing outer wall cause headspace sweating.'
});

// 3. Create Spoilage Hazard Nodes
CREATE (s1:SpoilageType {
    name: 'Aspergillus flavus (Aflatoxin B1)',
    category: 'Fungal Pathogen / Mycotoxin',
    optimum_temp_min: 25.0,
    optimum_temp_max: 37.0,
    optimum_rh_min: 80.0,
    danger_level: 'CRITICAL',
    recommended_action: 'Perform immediate batch separation, run dry-air aeration when RH < 60%, and test for aflatoxin ppm before mandi shipment.'
})
CREATE (s2:SpoilageType {
    name: 'Penicillium Verrucosum (Ochratoxin)',
    category: 'Storage Mold',
    optimum_temp_min: 18.0,
    optimum_temp_max: 28.0,
    optimum_rh_min: 78.0,
    danger_level: 'HIGH',
    recommended_action: 'Immediately halt external vent intake if outside RH > 75%; activate bottom-to-top forced dry aeration.'
})
CREATE (s3:SpoilageType {
    name: 'Grain Self-Heating Hotspot (Thermogenesis)',
    category: 'Biochemical Breakdown',
    optimum_temp_min: 30.0,
    optimum_temp_max: 55.0,
    optimum_rh_min: 65.0,
    danger_level: 'HIGH',
    recommended_action: 'Rotate and turn the core grain stack; operate aeration fan continuously to dissipate thermal build-up.'
})
CREATE (s4:SpoilageType {
    name: 'Sitophilus oryzae (Rice Weevil Infestation)',
    category: 'Insect Pest',
    optimum_temp_min: 26.0,
    optimum_temp_max: 35.0,
    optimum_rh_min: 60.0,
    danger_level: 'MEDIUM',
    recommended_action: 'Cool the grain mass below 18°C via nocturnal aeration to suppress insect egg development and respiration.'
})
CREATE (s5:SpoilageType {
    name: 'Moisture Migration & Headspace Sweating',
    category: 'Physical Condensation',
    optimum_temp_min: 10.0,
    optimum_temp_max: 28.0,
    optimum_rh_min: 82.0,
    danger_level: 'HIGH',
    recommended_action: 'Engage roof exhaust fans to equalize headspace temperature and prevent surface caking.'
});

// 4. Create Grain Type Nodes
CREATE (g1:GrainType {
    name: 'Wheat (HD-2967)',
    family: 'Cereal',
    max_safe_mc: 13.5,
    critical_mc: 14.5,
    market_value_inr_qtl: 2275
})
CREATE (g2:GrainType {
    name: 'Paddy (PB-1121)',
    family: 'Cereal',
    max_safe_mc: 13.0,
    critical_mc: 14.0,
    market_value_inr_qtl: 3850
})
CREATE (g3:GrainType {
    name: 'Maize (Hybrid)',
    family: 'Cereal',
    max_safe_mc: 13.5,
    critical_mc: 14.5,
    market_value_inr_qtl: 2090
});

// 5. Connect Regional Climate Relationships
CREATE (r1)-[:EXPERIENCES]->(c1)
CREATE (r1)-[:EXPERIENCES]->(c2)
CREATE (r1)-[:EXPERIENCES]->(c3)
CREATE (r1)-[:EXPERIENCES]->(c4)
CREATE (r2)-[:EXPERIENCES]->(c1)
CREATE (r2)-[:EXPERIENCES]->(c2)
CREATE (r3)-[:EXPERIENCES]->(c1)
CREATE (r3)-[:EXPERIENCES]->(c3);

// 6. Connect Climate Events to Spoilage Hazards
CREATE (c1)-[:TRIGGERS {severity: 'HIGH', min_temp: 26.0, min_rh: 72.0, historical_incidence_score: 0.88}]->(s1)
CREATE (c1)-[:TRIGGERS {severity: 'HIGH', min_temp: 24.0, min_rh: 70.0, historical_incidence_score: 0.82}]->(s2)
CREATE (c1)-[:TRIGGERS {severity: 'MEDIUM', min_temp: 28.0, min_rh: 65.0, historical_incidence_score: 0.74}]->(s4)

CREATE (c2)-[:TRIGGERS {severity: 'HIGH', min_temp: 20.0, min_rh: 75.0, historical_incidence_score: 0.85}]->(s2)
CREATE (c2)-[:TRIGGERS {severity: 'HIGH', min_temp: 22.0, min_rh: 78.0, historical_incidence_score: 0.81}]->(s5)

CREATE (c3)-[:TRIGGERS {severity: 'HIGH', min_temp: 34.0, min_rh: 50.0, historical_incidence_score: 0.80}]->(s3)
CREATE (c3)-[:TRIGGERS {severity: 'HIGH', min_temp: 29.0, min_rh: 55.0, historical_incidence_score: 0.78}]->(s4)

CREATE (c4)-[:TRIGGERS {severity: 'HIGH', min_temp: 8.0, min_rh: 80.0, historical_incidence_score: 0.76}]->(s5);

// 7. Connect Grain Types Susceptibility
CREATE (g1)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.90}]->(s1)
CREATE (g1)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.85}]->(s3)
CREATE (g1)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.82}]->(s4)

CREATE (g2)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.92}]->(s1)
CREATE (g2)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.88}]->(s2)
CREATE (g2)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.86}]->(s5)

CREATE (g3)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.95}]->(s1)
CREATE (g3)-[:SUSCEPTIBLE_TO {vulnerability_weight: 0.80}]->(s3);
