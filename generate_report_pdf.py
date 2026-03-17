import os
from fpdf import FPDF

class ProjectReportPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, 'DCIT 403 Crop Disease Intelligent Agent Project Report', 0, 0, 'C')
            self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = ProjectReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Paths
    brain_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\b34e3501-2ed3-4089-bfcd-c2274a685cc8"
    img_goals = os.path.join(brain_dir, "goal_hierarchy_diagram_1773341332729.png")
    img_caps = os.path.join(brain_dir, "capability_grouping_diagram_1773341348464.png")
    img_acq = os.path.join(brain_dir, "acquaintance_diagram_1773341363082.png")
    img_int = os.path.join(brain_dir, "interaction_diagram_1773341482787.png")

    # Title Page
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 24)
    pdf.ln(40)
    pdf.cell(0, 20, 'DCIT 403 Semester Project Report', 0, 1, 'C')
    pdf.set_font('helvetica', 'B', 18)
    pdf.cell(0, 10, 'University of Ghana', 0, 1, 'C')
    pdf.ln(20)
    pdf.set_font('helvetica', 'B', 20)
    pdf.cell(0, 15, 'Crop Disease Intelligent Agent', 0, 1, 'C')
    pdf.ln(50)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, 'Design and Implementation following Prometheus Methodology', 0, 1, 'C')
    
    # Table of Contents
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'TABLE OF CONTENTS', 0, 1)
    pdf.set_font('helvetica', '', 12)
    toc = [
        "1. Introduction", "2. System Analysis", "3. Architectural Design",
        "4. Interaction Design", "5. Detailed Design", "6. Implementation",
        "7. Conclusion", "8. References"
    ]
    for item in toc:
        pdf.cell(0, 8, item, 0, 1)

    # 1. Introduction
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '1. INTRODUCTION', 0, 1)
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, '1.1 Problem Statement', 0, 1)
    pdf.set_font('helvetica', '', 12)
    text = (
        "Crop diseases are responsible for an estimated 10-16% annual loss in global agricultural production, "
        "costing billions of dollars and threatening food security. Smallholder farmers-who produce over 70% "
        "of the world's food-are disproportionately affected because they lack timely access to expert plant "
        "pathologists. By the time a farmer visually identifies a disease, significant yield damage may have already occurred."
    )
    pdf.multi_cell(0, 8, text)
    pdf.ln(5)

    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, '1.2 Why an Agent-Based Approach?', 0, 1)
    pdf.set_font('helvetica', '', 12)
    text = (
        "An agent-based approach is ideal for this problem because the system must demonstrate autonomy, "
        "reactivity, proactiveness, and goal-directed behaviour-properties that distinguish agents from traditional software applications."
    )
    pdf.multi_cell(0, 8, text)
    
    # Agent Properties Table
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 10, 'Agent Property', 1)
    pdf.cell(150, 10, 'How It Applies', 1, 1)
    pdf.set_font('helvetica', '', 11)
    table_data = [
        ("Autonomy", "The agent independently processes images without human intervention"),
        ("Reactivity", "It reacts to new image inputs (percepts) in real time"),
        ("Proactiveness", "It pursues the goal of accurate diagnosis and can escalate cases"),
        ("Goal-directed", "It has clear goals: accuracy, actionable treatment, and flagging uncertainty")
    ]
    for prop, app in table_data:
        pdf.cell(40, 10, prop, 1)
        pdf.cell(150, 10, app, 1, 1)

    # 2. System Analysis
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '2. SYSTEM ANALYSIS', 0, 1)
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, '2.1 Goal Specification', 0, 1)
    
    if os.path.exists(img_goals):
        pdf.image(img_goals, x=20, w=170)
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, 'Figure 1: Goal Hierarchy Diagram', 0, 1, 'C')
    
    # 3. Architectural Design
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '3. ARCHITECTURAL DESIGN', 0, 1)
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, '3.2 Capability Grouping', 0, 1)
    if os.path.exists(img_caps):
        pdf.image(img_caps, x=20, w=170)
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, 'Figure 2: Functionality Grouping Diagram', 0, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, '3.3 Acquaintance Diagram', 0, 1)
    if os.path.exists(img_acq):
        pdf.image(img_acq, x=20, w=170)
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, 'Figure 3: Acquaintance Diagram', 0, 1, 'C')

    # 4. Interaction Design
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '4. INTERACTION DESIGN', 0, 1)
    if os.path.exists(img_int):
        pdf.image(img_int, x=20, w=170)
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, 'Figure 4: Sequence Interaction Diagram', 0, 1, 'C')

    # 5. Detailed Design & Implementation
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '5. DETAILED DESIGN', 0, 1)
    pdf.set_font('helvetica', '', 12)
    pdf.multi_cell(0, 8, "The detailed design covers the BDI loop (Perceive-Decide-Act) implemented in Python. "
                          "Capabilities include Perception, Classification, and Treatment Recommendation.")
    
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '6. IMPLEMENTATION', 0, 1)
    pdf.multi_cell(0, 8, "The implementation utilizes PyTorch for the CNN pipeline and a dedicated BDI orchestrator "
                          "in agent.py. The environment is simulated via environment.py to demonstrate autonomy.")

    # Conclusion
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, '7. CONCLUSION', 0, 1)
    pdf.set_font('helvetica', '', 12)
    pdf.multi_cell(0, 8, "The Crop Disease Intelligent Agent successfully maps the Prometheus methodology to "
                          "a real-world domain, providing a robust, autonomous solution for food security.")

    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    output_path = os.path.join(desktop_path, "Crop_Disease_Agent_Project_Report.pdf")
    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")

if __name__ == "__main__":
    create_pdf()
