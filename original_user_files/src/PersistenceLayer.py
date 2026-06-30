import sqlite3

class PersistenceLayer: 
    def __init__(self,db_path="hestia.db"):
        self.db_path = db_path
    
    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        return conexion
    
    def crear_usuario(self,name,profile_type):
        conexion = self.conectar() 
        cursor = conexion.cursor()
    
        cursor.execute("""
                    INSERT INTO user_profile (name,profile_type)
                    VAlues(?,?)
                    """,(name,profile_type))
        conexion.commit()
        id_user = cursor.lastrowid
        conexion.close()
        return id_user
    
    def load_user(self,id_user):
        conexion = self.conectar()
        cursor = conexion.cursor()
            
        cursor.execute("""
                    SELECT id_user,name,profile_type,created_at
                    FROM user_profile
                    where id_user = ?
                    """, (id_user,))
        usuario = cursor.fetchone()
        conexion.close()
        return usuario
    def save_skill_state(
        self,
        id_user,
        skill_id,
        p_l_operativo,
        p_l_teorico,
        p_t,
        p_g,
        p_s,
        avg_time_ms
    ):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("""
                    INSERT into Skill_state (
                    id_user,
                skill_id,
                p_l_operativo,
                p_l_teorico,
                p_t,
                p_g,
                p_s,
                avg_time_ms
                    )
                    VALUES (?,?,?,?,?,?,?,?)
                    """, (id_user,
        skill_id,
        p_l_operativo,
        p_l_teorico,
        p_t,
        p_g,
        p_s,
        avg_time_ms
            ))
        conexion.commit()
        conexion.close()
    def load_skill_state(self,id_user,skill_id):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT *FROM skill_state Where id_user = ? and skill_id = ? Order BY updated_at DESC LIMIT 1 ",(id_user,skill_id))
        estado = cursor.fetchone()
        conexion.close()
        return estado
    
    def save_method_state(self,id_user,method_id,q_value,timed_used):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("INSERT INTO method_state (id_user,method_id,q_value,times_used) VALUES (?,?,?,?)",(id_user,method_id,q_value,timed_used))
        
        conexion.commit()
        conexion.close()
    
    def log_response(self,id_user,exercise_id,skill_id,method_id,is_correct,response_time_ms):
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("INSERT INTO response_log (id_user,exercise_id,skill_id,method_id,is_correct, response_time_ms) VALUES (?,?,?,?,?,?)",(id_user,exercise_id,skill_id,method_id,is_correct,response_time_ms))
        
        conexion.commit()
        conexion.close()