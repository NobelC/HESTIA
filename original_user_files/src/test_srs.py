from SRSQueue import SRSQueue

srs = SRSQueue("hestia.db")

id_user = 1
skill_id = "vocal_a"

srs.schedule_next(id_user, skill_id, 0)

skills = srs.get_due_skills(id_user)

print("Habilidades pendientes de repaso:")
print(skills)

srs.mark_reviewed(id_user, skill_id, True)

print("Repaso marcado correctamente.")