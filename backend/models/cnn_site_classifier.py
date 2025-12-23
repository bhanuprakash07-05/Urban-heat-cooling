def sample_site_classification(zone="zone-1"):
    mapping = {
        "zone-1": {"zone_id": zone, "predicted_class": "residential", "confidence": 0.85},
        "zone-2": {"zone_id": zone, "predicted_class": "commercial", "confidence": 0.8},
    }
    return mapping.get(zone, {"zone_id": zone, "predicted_class": "mixed", "confidence": 0.75})
