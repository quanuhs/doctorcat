from MyData import db, client

class User:
    def __init__(self, data):
        self._id = data["_id"]
        self.platform = data["platform"]
        self.user_id = data["userID"]
        self.status = data["status"]
        self.additional_status = data["additional"]
        self.task = data["task"]
        self.has_task = data["hasTask"]
        self.description = self.task.get("description")
        self.doctors_id = self.task.get("doctorsID")
        self.notify = data["notify"]

        if self.status == 'b' and self.doctors_id != "":
            self.in_conversation = True
        else:
            self.in_conversation = False

    def update_doctor(self, new_id):
        self.doctors_id = new_id
        db.users.update_one({"_id": self._id}, {"$set": {"task.doctorsID": new_id}})

    def update_status(self, new_status):
        self.status = new_status
        db.users.update_one({"_id": self._id}, {"$set": {"status": new_status}})

    def update_additional_status(self, new_additional_status):
        self.additional_status = new_additional_status
        db.users.update_one({"_id": self._id}, {"$set": {"additional": new_additional_status}})

    def create_token(self):
        self.update_description(self.additional_status)
        self.update_additional_status("")
        db.users.update_one({"_id": self._id}, {"$set": {"hasTask": True}})

    def update_description(self, description):
        self.description = description
        db.users.update_one({"_id": self._id}, {"$set": {"task.description": description}})

    def update_notify(self, status):
        self.notify = status
        db.users.update_one({"_id": self._id}, {"$set": {"notify": status}})

    def delete(self):
        if self.in_conversation:
            db.doctors.update_one({"_id": self.doctors_id}, {"$set": {"patientID": ""}})


        db.users.delete_one({"_id": self._id})