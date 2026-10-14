import unittest
import json
from server.router import route_request

class TestProtocolAndRouter(unittest.TestCase):
    
    def test_protocol_serialization(self):
        """Prova la serialització i deserialització del protocol JSON"""
        request_dict = {"action": "ping", "data": {"msg": "hola"}}
        
        # Simulem l'enviament (Client)
        request_bytes = json.dumps(request_dict).encode('utf-8')
        self.assertIsInstance(request_bytes, bytes)
        
        # Simulem la recepció (Servidor)
        decoded_str = request_bytes.decode('utf-8')
        decoded_dict = json.loads(decoded_str)
        self.assertEqual(decoded_dict["action"], "ping")
        self.assertEqual(decoded_dict["data"]["msg"], "hola")

    def test_router_valid_action(self):
        """Prova que el router dirigeix bé una acció vàlida"""
        response = route_request("ping", {"test": "data"})
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "Pong! Comunicació correcta.")

    def test_router_invalid_action(self):
        """Prova com el router gestiona accions desconegudes"""
        response = route_request("accion_inventada", {})
        self.assertEqual(response["status"], "error")
        self.assertIn("no implementada", response["message"])

if __name__ == '__main__':
    unittest.main()