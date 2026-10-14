# Protocol de Comunicació Client/Servidor TCP

Aquest projecte utilitza un protocol personalitzat basat en **JSON sobre TCP** per a la comunicació entre el client i el servidor. L'arquitectura utilitza sockets bloquejants estàndard de Python.

## 1. Estructura de la Petició (Request)
El client envia les peticions en format JSON codificat en `utf-8`. L'estructura estàndard conté el nom de l'acció i un diccionari amb les dades necessàries:

```json
{
  "action": "nom_de_l_operacio",
  "data": {
    "parametre1": "valor1"
  }
}
```

## 2. Estructura de la Resposta (Response)
El servidor retorna sempre un JSON codificat en `utf-8` amb el resultat de l'operació. Aquesta resposta inclou l'estat, un missatge descriptiu i les dades sol·licitades (traduïdes a DTOs per aïllar la base de dades):

```json
{
  "status": "success | error",
  "message": "Missatge de confirmació o descripció de l'error",
  "data": [ ... ] 
}
```

## 3. Operacions Suportades (CRUD)
L'enrutador del servidor (`router.py`) suporta les següents accions:

1. **`ping`**: Comprovació bàsica de connexió (Echo). Retorna el mateix missatge enviat.
2. **`create_platform`**: Crea una nova plataforma. 
   - *Requereix*: `name` a dins de `data`.
3. **`create_game`**: Crea un nou joc associat a una plataforma. 
   - *Requereix*: `title`, `price` i `platform_id`.
4. **`list_games`**: Retorna la llista completa de jocs guardats a la base de dades.
5. **`delete_game`**: Esborra un joc existent. 
   - *Requereix*: `game_id`.

## 4. Gestió d'Errors
* Si el servidor rep una cadena que no és un JSON vàlid, retorna un error de format.
* Si l'acció sol·licitada no existeix, es retorna un error amb el missatge "Acció no implementada".
* Els errors interns de la base de dades es capturen mitjançant blocs `try/except` per evitar que el servidor caigui, i es retorna el detall a l'atribut `message` amb un `status: "error"`.