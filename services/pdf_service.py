"""PDF generation service using WeasyPrint"""
import os
from datetime import datetime
from weasyprint import HTML, CSS
from flask import render_template_string

def generate_pdf_report(client_info, intake_data, explanation, quote_result):
    """Generate PDF report of top 3 plan recommendations"""
    
    # Get agent info (mock for now)
    agent_info = {
        'name': 'Agent Demo',
        'company': 'Plan Concierge',
        'phone': '(555) 123-4567',
        'email': 'agent@plansconcierge.com'
    }
    
    # Prepare data for template
    template_data = {
        'agent': agent_info,
        'client': client_info,
        'intake': intake_data,
        'explanation': explanation,
        'quote_result': quote_result,
        'generated_date': datetime.now().strftime('%B %d, %Y'),
        'plan_year': intake_data.get('plan_year', 2024)
    }
    
    # HTML template for PDF
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ACA Plan Recommendations</title>
        <style>
            @page {
                size: A4;
                margin: 0.75in;
                @bottom-right {
                    content: "Page " counter(page) " of " counter(pages);
                }
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 11pt;
                line-height: 1.4;
                color: #333;
            }
            
            .header {
                border-bottom: 3px solid #2c5aa0;
                padding-bottom: 15px;
                margin-bottom: 25px;
            }
            
            .company-name {
                font-size: 24pt;
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 5px;
            }
            
            .agent-info {
                font-size: 10pt;
                color: #666;
            }
            
            .client-section {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            
            .section-title {
                font-size: 14pt;
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 10px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }
            
            .plan-card {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                page-break-inside: avoid;
            }
            
            .plan-rank {
                background-color: #2c5aa0;
                color: white;
                width: 25px;
                height: 25px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                margin-right: 10px;
            }
            
            .plan-title {
                font-size: 13pt;
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 8px;
            }
            
            .premium-highlight {
                font-size: 18pt;
                font-weight: bold;
                color: #28a745;
                margin: 10px 0;
            }
            
            .pro-con-lists {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 10px 0;
            }
            
            .pros li {
                color: #28a745;
            }
            
            .cons li {
                color: #dc3545;
            }
            
            .disclaimer {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 5px;
                margin-top: 25px;
                font-size: 10pt;
            }
            
            .footer {
                margin-top: 30px;
                text-align: center;
                font-size: 9pt;
                color: #666;
            }
            
            .citation {
                font-size: 9pt;
                color: #666;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-name">{{ agent.company }}</div>
            <div class="agent-info">
                {{ agent.name }} • {{ agent.phone }} • {{ agent.email }}
            </div>
        </div>
        
        <div class="client-section">
            <div class="section-title">Client Information</div>
            <strong>{{ client.first_name }} {{ client.last_name }}</strong><br>
            {{ intake.zip }}, {{ intake.county }}, {{ intake.state }}<br>
            Household Size: {{ intake.household_size }} • Annual Income: ${{ "{:,}".format(intake.income) }}<br>
            Plan Year: {{ plan_year }}
        </div>
        
        <div class="section-title">Plan Recommendations</div>
        <p>{{ explanation.summary }}</p>
        
        {% if quote_result.aptc > 0 %}
        <p><strong>Good news!</strong> You qualify for ${{ "%.2f"|format(quote_result.aptc) }}/month in premium tax credits.</p>
        {% endif %}
        
        {% for plan in explanation.plan_explanations %}
        <div class="plan-card">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span class="plan-rank">{{ plan.rank }}</span>
                <span class="plan-title">{{ plan.title }}</span>
            </div>
            
            <div class="premium-highlight">
                ${{ "%.2f"|format(quote_result.top_3[plan.rank - 1].net_premium) }}/month
            </div>
            
            <p>{{ plan.explanation }}</p>
            
            <div class="pro-con-lists">
                <div>
                    <strong>Advantages:</strong>
                    <ul class="pros">
                    {% for pro in plan.pros %}
                        <li>{{ pro }}</li>
                    {% endfor %}
                    </ul>
                </div>
                <div>
                    <strong>Considerations:</strong>
                    <ul class="cons">
                    {% for con in plan.cons %}
                        <li>{{ con }}</li>
                    {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
        {% endfor %}
        
        <div class="section-title">Plan Comparison</div>
        <p>{{ explanation.comparison }}</p>
        
        <div class="section-title">Key Terms</div>
        {% for citation in explanation.citations %}
        <div class="citation">
            <strong>{{ citation.term }}:</strong> {{ citation.definition }}
            <br><em>Source: {{ citation.source_url }}</em>
        </div>
        {% endfor %}
        
        <div class="section-title">Next Steps</div>
        <p>{{ explanation.next_steps }}</p>
        
        <div class="disclaimer">
            <strong>Important Disclaimer:</strong> {{ explanation.disclaimer }}
        </div>
        
        <div class="footer">
            Generated on {{ generated_date }} • Plan Concierge Analysis Report
        </div>
    </body>
    </html>
    """
    
    try:
        # Render HTML with data
        html_content = render_template_string(html_template, **template_data)
        
        # Convert to PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Return simple text-based report as fallback
        return generate_fallback_pdf(template_data)

def generate_fallback_pdf(template_data):
    """Generate simple text-based PDF when WeasyPrint fails"""
    
    simple_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ACA Plan Recommendations</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c5aa0; }}
            .plan {{ border: 1px solid #ccc; padding: 15px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <h1>{template_data['agent']['company']}</h1>
        <h2>Plan Recommendations for {template_data['client']['first_name']} {template_data['client']['last_name']}</h2>
        
        <p><strong>Summary:</strong> {template_data['explanation']['summary']}</p>
        
        <h3>Top 3 Recommended Plans:</h3>
    """
    
    for i, plan in enumerate(template_data['explanation']['plan_explanations']):
        simple_html += f"""
        <div class="plan">
            <h4>#{plan['rank']}: {plan['title']}</h4>
            <p><strong>Monthly Premium:</strong> ${template_data['quote_result']['top_3'][i]['net_premium']:.2f}</p>
            <p>{plan['explanation']}</p>
        </div>
        """
    
    simple_html += f"""
        <h3>Next Steps</h3>
        <p>{template_data['explanation']['next_steps']}</p>
        
        <p><em>{template_data['explanation']['disclaimer']}</em></p>
        
        <p><small>Generated on {template_data['generated_date']}</small></p>
    </body>
    </html>
    """
    
    try:
        html_doc = HTML(string=simple_html)
        return html_doc.write_pdf()
    except:
        # Ultimate fallback - return HTML as bytes
        return simple_html.encode('utf-8')
