"""
Classify holdings by industry sector using business descriptions
Run: python -m src.classify_industries
"""

import pandas as pd
import re

def classify_industry(description: str) -> str:
    """
    Classify business description into industry sector.
    Returns sector name or 'Unknown'.
    """
    if not description or pd.isna(description):
        return 'Unknown'

    desc_lower = description.lower()

    # Define industry keywords (order matters - more specific first)
    industry_map = {
        'Software/Technology': [
            'software', 'saas', 'platform', 'cloud', 'data analytics',
            'cybersecurity', 'it services', 'technology', 'digital',
            'erp', 'crm', 'artificial intelligence', 'machine learning',
            'app', 'mobile', 'internet', 'web', 'online', 'e-learning',
            'information technology', 'it solutions', 'tech', 'semiconductor'
        ],
        'Healthcare Services': [
            'healthcare', 'medical', 'hospital', 'clinical', 'patient',
            'pharmaceutical', 'drug', 'biotech', 'life sciences',
            'dental', 'veterinary', 'health insurance', 'physician',
            'healthcare services', 'medical device', 'healthcare equipment',
            'pharmacy', 'diagnostic', 'therapeutic', 'wellness'
        ],
        'Business Services': [
            'staffing', 'consulting', 'outsourcing', 'professional services',
            'human resources', 'payroll', 'marketing services', 'advertising',
            'business process', 'call center', 'customer service', 'research',
            'market research', 'analytics', 'legal services', 'accounting'
        ],
        'Financial Services': [
            'insurance', 'lending', 'financial', 'banking', 'payments',
            'wealth management', 'asset management', 'credit', 'fintech',
            'investment', 'brokerage', 'mortgage', 'payment processing'
        ],
        'Industrial/Manufacturing': [
            'manufacturing', 'industrial', 'equipment', 'machinery',
            'aerospace', 'defense', 'automotive', 'construction',
            'fabrication', 'metal', 'plastic', 'chemicals', 'materials',
            'electrical', 'mechanical', 'tools', 'components', 'parts'
        ],
        'Consumer Products': [
            'consumer products', 'consumer goods', 'apparel', 'clothing',
            'fashion', 'footwear', 'accessories', 'beauty', 'cosmetics',
            'personal care', 'household products', 'furniture', 'home goods'
        ],
        'Food & Beverage': [
            'food', 'beverage', 'restaurant', 'dining', 'catering',
            'bakery', 'brewery', 'wine', 'spirits', 'coffee', 'snack',
            'grocery', 'culinary', 'nutrition'
        ],
        'Retail': [
            'retail', 'store', 'shop', 'e-commerce', 'ecommerce', 'merchant',
            'distribution', 'wholesaler', 'dealer'
        ],
        'Media & Entertainment': [
            'media', 'entertainment', 'broadcasting', 'publishing',
            'content', 'film', 'music', 'gaming', 'sports', 'events',
            'ticketing', 'production', 'creative', 'agency'
        ],
        'Education': [
            'education', 'school', 'training', 'learning', 'university',
            'college', 'educational', 'tutoring', 'curriculum'
        ],
        'Energy & Utilities': [
            'energy', 'oil', 'gas', 'power', 'utility', 'utilities',
            'renewable', 'solar', 'wind', 'pipeline', 'electric',
            'natural gas', 'petroleum', 'fuel'
        ],
        'Transportation & Logistics': [
            'logistics', 'transportation', 'shipping', 'freight',
            'trucking', 'warehouse', 'supply chain', 'distribution',
            'delivery', 'courier', 'aviation', 'airline', 'cargo'
        ],
        'Telecommunications': [
            'telecommunications', 'telecom', 'wireless', 'broadband',
            'network', 'communication', 'fiber', 'tower'
        ],
        'Real Estate': [
            'real estate', 'property', 'housing', 'commercial real estate',
            'residential', 'leasing', 'reit', 'facilities'
        ],
        'Hospitality': [
            'hospitality', 'hotel', 'resort', 'lodging', 'accommodation',
            'travel', 'tourism', 'venue'
        ],
        'Agriculture': [
            'agriculture', 'farming', 'agribusiness', 'crop', 'livestock',
            'agricultural', 'farm'
        ],
    }

    for industry, keywords in industry_map.items():
        if any(kw in desc_lower for kw in keywords):
            return industry

    return 'Other'


if __name__ == '__main__':
    print("=" * 60)
    print("CLASSIFYING HOLDINGS BY INDUSTRY")
    print("=" * 60)

    # Load holdings
    df = pd.read_csv('outputs/all_bdc_holdings.csv')
    print(f"\nLoaded {len(df):,} holdings")

    # Apply classification
    print("\nApplying industry classifier...")
    df['industry_sector'] = df['business_description'].apply(classify_industry)

    # Show classification results
    print("\nIndustry Distribution:")
    print("-" * 60)
    industry_counts = df['industry_sector'].value_counts()
    for industry, count in industry_counts.items():
        pct = count / len(df) * 100
        print(f"  {industry:30} {count:4} ({pct:5.1f}%)")

    # Save enriched data
    output_path = 'outputs/all_bdc_holdings_with_industry.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")

    # Show sample classifications
    print("\n" + "=" * 60)
    print("Sample Classifications:")
    print("=" * 60)
    sample = df[df['business_description'].notna()].head(15)
    for _, row in sample.iterrows():
        company = row['company_name'][:35]
        desc = row['business_description'][:40] if pd.notna(row['business_description']) else 'N/A'
        sector = row['industry_sector']
        print(f"{company:35} | {desc:40} | {sector}")
