# 09_Database_Design.md

# Database Design

## Core Entities

### User
- id
- name
- email

---

### Project
- id
- user_id
- name

---

### Session
- id
- project_id
- platform
- transcript
- timestamp

---

### DeveloperEvent
- id
- session_id
- event_type
- technology

---

### Memory
- id
- session_id
- content
- embedding_id

---

### Skill
- id
- user_id
- skill_name
- proficiency

---

### Recommendation
- id
- user_id
- recommendation
- type

---

### WeeklyReport
- id
- user_id
- generated_at