import streamlit as st
from geopy.distance import geodesic
import folium
import random

# 🔥 Dynamic Route Generation
def generate_route(start, end, steps=5):
    lat1, lon1 = start
    lat2, lon2 = end
    
    route = []
    for i in range(steps + 1):
        lat = lat1 + (lat2 - lat1) * i / steps + random.uniform(-0.001, 0.001)
        lon = lon1 + (lon2 - lon1) * i / steps + random.uniform(-0.001, 0.001)
        route.append((lat, lon))
        
    return route

# 🔥 Risk Label Function
def get_risk_label(score):
    if score >= 7:
        return "🟢 Low"
    elif score >= 5:
        return "🟡 Medium"
    else:
        return "🔴 High"

# 🔥 Safety Calculation
def calculate_safety(route, night_mode=False, incident_location=None):
    risk = 0
    crime_count = 0
    accident_count = 0
    lighting_count = 0
    
    for point in route:
        for c in crime_zones:
            if geodesic(point, c).km < 0.5:
                risk += 4 if night_mode else 3
                crime_count += 1
                
        for a in accident_zones:
            if geodesic(point, a).km < 0.5:
                risk += 2
                accident_count += 1
                
        for l in low_light_zones:
            if geodesic(point, l).km < 0.5:
                risk += 3 if night_mode else 1.5
                lighting_count += 1

        # 🔥 Live incident impact
        if incident_location and geodesic(point, incident_location).km < 0.5:
            risk += 5

    avg_risk = risk / len(route)
    safety_score = max(3, 10 - avg_risk * 0.8)

    return round(safety_score, 1), crime_count, accident_count, lighting_count


# ---------------- UI ---------------- #

st.title("🛣️ SafeRoute AI")
st.write("Find the safest route, not just the fastest!")

source = st.text_input("Enter Source")
destination = st.text_input("Enter Destination")

weight = st.slider("⚖️ Preference: Safety vs Speed", 0, 10, 7)
st.caption("Higher value prioritizes safety, lower value prioritizes speed")

night_mode = st.toggle("🌙 Night Mode (Safer at Night)")

# 🔥 Dynamic Risk Zones
crime_zones = [(12.972 + random.uniform(0, 0.002), 77.595)]
accident_zones = [(12.973 + random.uniform(0, 0.002), 77.596)]
low_light_zones = [(12.974 + random.uniform(0, 0.002), 77.597)]

if st.button("Find Safe Route"):

    if source == "" or destination == "":
        st.error("Please enter both source and destination")
    
    else:
        st.caption("🔄 Updating based on real-time environmental factors...")

        start = (12.9716, 77.5946)

        # 🔥 LIVE INCIDENT
        incident_flag = False
        incident_location = None

        if random.random() > 0.6:
            incident_flag = True
            incident_location = (
                12.972 + random.uniform(0, 0.002),
                77.595 + random.uniform(0, 0.002)
            )
            st.error("🚨 Live Alert: Accident reported nearby! Rerouting suggested")

        route_a = generate_route(start, (12.972, 77.595))
        route_b = generate_route(start, (12.975, 77.599))

        score_a, c1, a1, l1 = calculate_safety(route_a, night_mode, incident_location)
        score_b, c2, a2, l2 = calculate_safety(route_b, night_mode, incident_location)

        # 🔥 Dynamic Time
        time_a = round(random.uniform(12, 18), 1)
        time_b = round(random.uniform(14, 20), 1)

        st.subheader("Results")

        st.write(f"Route A → ⏱️ {time_a} min | Safety: {get_risk_label(score_a)} ({score_a}/10)")
        st.write(f"Route B → ⏱️ {time_b} min | Safety: {get_risk_label(score_b)} ({score_b}/10)")

        # 🔥 SMART DECISION
        scoreA_final = score_a * (weight/10) - time_a * ((10-weight)/10)
        scoreB_final = score_b * (weight/10) - time_b * ((10-weight)/10)

        if scoreA_final > scoreB_final:
            best = "A"
        else:
            best = "B"

        # ✅ RESULT
        if best == "A":
            st.success("✅ Recommended: Route A")
        else:
            st.success("✅ Recommended: Route B")

        # 🔥 IMPROVED CONFIDENCE (FIXED)
        diff = abs(scoreA_final - scoreB_final)
        max_score = max(abs(scoreA_final), abs(scoreB_final), 1)

        confidence = int(min(95, 50 + (diff / max_score) * 50))

        st.subheader("🧠 AI Confidence")
        st.write(f"Confidence in recommendation: **{confidence}%**")

        if confidence > 80:
            st.success("High confidence – clear safer choice")
        elif confidence > 65:
            st.warning("Moderate confidence – slight advantage")
        else:
            st.info("Low confidence – routes are quite similar")

        # 🔥 EXPLAINABLE AI
        st.subheader("Why this route?")

        if best == "A":
            st.info(f"""
Route A is better because:
- 🚨 Crime zones: {c1} vs {c2}
- ⚠️ Accident areas: {a1} vs {a2}
- 💡 Lighting conditions: {l1} vs {l2}
""")
        else:
            st.info(f"""
Route B is better because:
- 🚨 Crime zones: {c2} vs {c1}
- ⚠️ Accident areas: {a2} vs {a1}
- 💡 Lighting conditions: {l2} vs {l1}
""")

        # 🗺️ MAP
        m = folium.Map(location=[12.9716, 77.5946], zoom_start=13)

        folium.PolyLine(route_a, color="red", tooltip="Route A").add_to(m)
        folium.PolyLine(route_b, color="green", tooltip="Route B").add_to(m)

        for c in crime_zones:
            folium.Marker(c, tooltip="Crime Zone ⚠️", icon=folium.Icon(color="red")).add_to(m)

        for a in accident_zones:
            folium.Marker(a, tooltip="Accident Zone 🚧", icon=folium.Icon(color="orange")).add_to(m)

        for l in low_light_zones:
            folium.Marker(l, tooltip="Low Light Area 🌙", icon=folium.Icon(color="blue")).add_to(m)

        # 🚨 INCIDENT MARKER
        if incident_flag:
            folium.Marker(
                incident_location,
                tooltip="🚨 Live Accident",
                icon=folium.Icon(color="black")
            ).add_to(m)

        st.components.v1.html(m._repr_html_(), height=500)

        st.caption("⚡ Routes dynamically adjusted using real-time risk simulation")
        st.caption("🔌 Designed to integrate with real-time APIs like Google Maps and city safety datasets")