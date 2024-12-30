import streamlit as st
import json
import os
from typing import Dict, Any, List
import pandas as pd
from pydantic import BaseModel
from datetime import datetime

# Set page to wide mode
st.set_page_config(layout="wide")

class ComparisonResult(BaseModel):
    email_id: str
    selected_models: List[str] = []
    comparison_date: datetime = datetime.now()

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print(f"File not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def create_summary_table(data_dict: Dict[str, Dict]) -> pd.DataFrame:
    """Create summary comparison table"""
    model_stats = {
        'Model': list(data_dict.keys()),
        'Total Emails': [len(data) for data in data_dict.values()],
    }
    return pd.DataFrame(model_stats)

def load_selection_stats() -> Dict[str, int]:
    """Load model selection statistics"""
    try:
        if os.path.exists('selection_stats.json'):
            with open('selection_stats.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading selection stats: {e}")
    return {'OpenAI': 0, 'DeepSeek': 0, 'LLaMA': 0, 'Qwen': 0}

def update_selection_stats(model: str):
    """Update and save selection statistics for a single model"""
    stats = load_selection_stats()
    stats[model] = stats.get(model, 0) + 1
    
    try:
        with open('selection_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving selection stats: {e}")

def save_model_selection(email_id: str, model: str, results_file: str = "comparison_results.json"):
    """Save individual model selection"""
    try:
        # Load existing results
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {}

        # Update or initialize the selection for this email
        if email_id not in results:
            results[email_id] = {"selected_models": [], "comparison_date": str(datetime.now())}
        
        if model not in results[email_id]["selected_models"]:
            results[email_id]["selected_models"].append(model)
            
        # Save updated results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        # Update selection stats
        update_selection_stats(model)
        return True
    except Exception as e:
        print(f"Error saving selection: {e}")
        return False

def main():
    st.title("Email Analysis Comparison")

    # Load data for all models
    model_data = {
        'OpenAI': load_json_data('analyzed_emails_openai.json'),
        'DeepSeek': load_json_data('analyzed_emails_deepseek.json'),
        'LLaMA': load_json_data('analyzed_emails_llama.json'),
        'Qwen': load_json_data('analyzed_emails_qwen.json')
    }

    # Display summary tables
    st.subheader("Analysis Summary")
    summary_df = create_summary_table(model_data)
    st.dataframe(summary_df, use_container_width=True)

    # Display selection statistics
    st.subheader("Model Selection Statistics")
    stats = load_selection_stats()
    stats_df = pd.DataFrame([stats]).T.reset_index()
    stats_df.columns = ['Model', 'Times Selected']
    st.dataframe(stats_df, use_container_width=True)

    # Get common email IDs across all models
    email_ids = set(model_data['OpenAI'].keys())
    for data in model_data.values():
        email_ids = email_ids.intersection(set(data.keys()))
    email_ids = sorted(list(email_ids))

    # Detailed comparison for all emails
    st.subheader("Detailed Comparisons")

    # Load existing selections
    try:
        with open("comparison_results.json", 'r') as f:
            existing_selections = json.load(f)
    except:
        existing_selections = {}

    # Display all emails
    for idx, email_id in enumerate(email_ids, 1):
        st.markdown(f"### Email #{idx} ({email_id})")
        
        # Create columns for each model
        cols = st.columns(len(model_data))
        
        # Show selected models for this email
        selected_models = existing_selections.get(email_id, {}).get("selected_models", [])
        if selected_models:
            st.info(f"Selected models: {', '.join(selected_models)}")

        for col, (model_name, model_results) in zip(cols, model_data.items()):
            with col:
                st.markdown(f"#### {model_name}")
                if email_id in model_results:
                    data = model_results[email_id]
                    
                    # Model selection button
                    if st.button(f"Select {model_name}", 
                               key=f"{model_name}_button_{email_id}",
                               type="primary" if model_name in selected_models else "secondary"):
                        if save_model_selection(email_id, model_name):
                            st.success(f"Selected {model_name}")
                            st.rerun()
                    
                    # Display all fields
                    for field, value in data.items():
                        st.text_area(
                            f"{field}", 
                            str(value),
                            height=150 if field.startswith('post_content') else 100,
                            key=f"{model_name}_{field}_{email_id}"
                        )
        
        st.markdown("---")  # Add separator between emails

if __name__ == "__main__":
    main() 