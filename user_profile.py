import streamlit as st

# Sidebar User Preference Settings 
def user_preferences():
    # Main Therapeutic Areas
    fields = ["Oncology", "Cardiology", "Neurology", "Pediatrics", "Other"]

    # Subfields for each Therapeutic Area
    subfields = {
        "Oncology": ["Breast Cancer", "Lung Cancer", "Leukemia"],
        "Cardiology": ["Heart Failure", "Arrhythmia", "Hypertension"],
        # Add more subfields for other fields
    }

    # Get preferred fields
    preferred_fields = st.sidebar.multiselect("Select your preferred fields:", fields)

    # Initialize a dictionary to store preferred subfields for each field
    preferred_subfields = {}

    # Loop through the selected preferred fields
    for field in preferred_fields:
        if field == "Other":
            # Free text input for additional fields
            freetext_field = st.sidebar.text_input(f"Enter additional field:")
            preferred_subfields[freetext_field] = []
        else:
            # Get available subfields for the selected field
            available_subfields = subfields.get(field, []) + ["Other"]

            # Display a multiselect widget for each selected field's subfields
            selected_subfields = st.sidebar.multiselect(f"Select specific areas of interest for {field}:", available_subfields)

            # Check if "Other" is selected for subfields
            if "Other" in selected_subfields:
                # Add a text input for freetext option
                freetext_subfield = st.sidebar.text_input(f"Enter additional areas for {field}:")
                # Append freetext subfield to selected subfields
                selected_subfields.append(freetext_subfield)
                selected_subfields.remove("Other")  # Remove "Other" from the list

            # Store the selected subfields in the dictionary
            preferred_subfields[field] = selected_subfields

    return preferred_fields, preferred_subfields

