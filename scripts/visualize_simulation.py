import sys
import os
import random

# Add the build/backend directory to sys.path so we can import the compiled hestia_core module
build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build', 'backend'))
sys.path.append(build_dir)

try:
    import hestia_core as hc  # type: ignore
except ImportError as e:
    print(f"Failed to import hestia_core from {build_dir}. Ensure it is compiled.")
    raise e

def run_simulation(scenario_name, p_true, iterations, lambda_val=0.5):
    print(f"Running simulation: {scenario_name} (iterations={iterations}, P(correct)={p_true})")
    
    engine = hc.bkt.BKTEngine()
    mab = hc.mab.MABEngine(1.0)
    session = hc.bkt.SessionManager()
    blender = hc.zone.ZoneBlender(42)
    import sqlite3
    db_path = "test_sim.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA user_version = 2;")
    conn.execute("CREATE TABLE skill_state (student_id INT, skill_id INT, p_learn_operative REAL, p_learn_theorical REAL, p_transition REAL, p_slip REAL, p_guess REAL, p_forget REAL, avg_response_time REAL, last_practice_time INT, PRIMARY KEY(student_id, skill_id));")
    conn.execute("CREATE TABLE method_state (student_id INT, skill_id INT, method_id INT, attempts INT, successes INT, PRIMARY KEY(student_id, skill_id, method_id));")
    conn.execute("CREATE TABLE response_log (student_id INT, skill_id INT, method_id INT, timestamp INT, is_correct INT, response_ms INT, p_learn REAL);")
    conn.execute("CREATE TABLE srs_state (student_id INT, skill_id INT, correct_streak INT, next_review INT, PRIMARY KEY(student_id, skill_id));")
    conn.close()
    
    storage = hc.persistence.PersistenceLayer.create(db_path)
    if storage is None:
        raise Exception("Failed to initialize PersistenceLayer")
        
    graph = hc.graph.SkillGraph()
    srs = hc.srs.SRSQueue()
    
    processor = hc.core.ResponseProcessor(
        engine, mab, session, storage, blender, graph, srs, lambda_val
    )
    student_id = 1
    skill_id = 1
    state = hc.bkt.SkillState()
    processor.start_session(state)
    
    iter_idx = []
    pL_operative = []
    pL_theorical = []
    
    for i in range(iterations):
        correct = random.random() < p_true
        response_ms = random.uniform(400.0, 1500.0)
        result = processor.process_response(student_id, skill_id, hc.mab.METHOD.VISUAL, correct, response_ms)
        
        iter_idx.append(i + 1)
        pL_operative.append(result.current_pL)
        pL_theorical.append(result.current_pL_theorical)
        
    processor.end_session(state)
    return iter_idx, pL_operative, pL_theorical

def generate_svg(iter_idx, pL_op, pL_th, scenario_name):
    width, height = 800, 400
    margin = 50
    graph_width = width - 2 * margin
    graph_height = height - 2 * margin
    
    def map_x(x): return margin + (x - min(iter_idx)) / max(1, (max(iter_idx) - min(iter_idx))) * graph_width
    def map_y(y): return margin + graph_height - (y * graph_height)
    
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background-color: white; font-family: sans-serif;">']
    
    # Background and Title
    svg.append(f'<text x="{width/2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">HESTIA BKT Learning Curve: {scenario_name}</text>')
    
    # Grid and Axes
    svg.append(f'<rect x="{margin}" y="{margin}" width="{graph_width}" height="{graph_height}" fill="none" stroke="#ddd" />')
    for y_val in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pos = map_y(y_val)
        svg.append(f'<line x1="{margin}" y1="{y_pos}" x2="{width-margin}" y2="{y_pos}" stroke="#eee" />')
        svg.append(f'<text x="{margin-10}" y="{y_pos+4}" text-anchor="end" font-size="10">{y_val:.1f}</text>')
    
    # Reference lines
    svg.append(f'<line x1="{margin}" y1="{map_y(0.98)}" x2="{width-margin}" y2="{map_y(0.98)}" stroke="grey" stroke-dasharray="5,5" />')
    svg.append(f'<text x="{width-margin+5}" y="{map_y(0.98)+4}" font-size="10" fill="grey">0.98 (Cap)</text>')
    svg.append(f'<line x1="{margin}" y1="{map_y(0.90)}" x2="{width-margin}" y2="{map_y(0.90)}" stroke="green" stroke-dasharray="5,5" />')
    svg.append(f'<text x="{width-margin+5}" y="{map_y(0.90)+4}" font-size="10" fill="green">0.90 (Mastery)</text>')
    
    # Plot Theoretical
    th_points = " ".join([f"{map_x(x)},{map_y(y)}" for x, y in zip(iter_idx, pL_th)])
    svg.append(f'<polyline points="{th_points}" fill="none" stroke="red" stroke-width="2" stroke-dasharray="4,4" opacity="0.7" />')
    
    # Plot Operative
    op_points = " ".join([f"{map_x(x)},{map_y(y)}" for x, y in zip(iter_idx, pL_op)])
    svg.append(f'<polyline points="{op_points}" fill="none" stroke="blue" stroke-width="2" />')
    for x, y in zip(iter_idx, pL_op):
        svg.append(f'<circle cx="{map_x(x)}" cy="{map_y(y)}" r="3" fill="blue" />')
    
    # Legend
    svg.append(f'<rect x="{margin+10}" y="{margin+10}" width="140" height="40" fill="white" stroke="#ccc" />')
    svg.append(f'<line x1="{margin+15}" y1="{margin+20}" x2="{margin+35}" y2="{margin+20}" stroke="blue" stroke-width="2" />')
    svg.append(f'<text x="{margin+40}" y="{margin+24}" font-size="10">Operative P(L)</text>')
    svg.append(f'<line x1="{margin+15}" y1="{margin+40}" x2="{margin+35}" y2="{margin+40}" stroke="red" stroke-width="2" stroke-dasharray="4,4" />')
    svg.append(f'<text x="{margin+40}" y="{margin+44}" font-size="10">Theoretical P(L)</text>')
    
    svg.append('</svg>')
    
    filename = f"simulation_{scenario_name.lower().replace(' ', '_')}.svg"
    with open(filename, 'w') as f:
        f.write("\n".join(svg))
    print(f"Saved SVG plot to {filename}")

def main():
    random.seed(42)
    
    iters, pL_op, pL_th = run_simulation("Random Clicker", p_true=0.50, iterations=100)
    generate_svg(iters, pL_op, pL_th, "Random Clicker")
    
    iters, pL_op, pL_th = run_simulation("Perfect Learner", p_true=1.0, iterations=20)
    generate_svg(iters, pL_op, pL_th, "Perfect Learner")

if __name__ == "__main__":
    main()
