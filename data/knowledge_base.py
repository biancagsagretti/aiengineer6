"""Base de conocimiento simulada (reemplazable por tu Vector DB de pre-entregas anteriores).

Para conectar tu Chroma/FAISS/Pinecone, reemplazá `search_knowledge_base`
en tools/research_tools.py por una llamada a `vectorstore.similarity_search(query, k)`.
"""

KNOWLEDGE_BASE = [
    {
        "id": "doc-001",
        "title": "Reseñas de clientes - auriculares AuraPods",
        "text": (
            "Reseñas de clientes del producto AuraPods (auriculares inalámbricos). "
            "R1 (Calificación 5/5): Excelente sonido, la batería dura todo el día. Totalmente recomendable. "
            "R2 (Calificación 4/5): Muy buena calidad de audio, aunque el estuche es un poco grande. "
            "R3 (Calificación 2/5): La conexión bluetooth es mala y se corta seguido. Decepcionante. "
            "R4 (Calificación 5/5): Cómodos y livianos, la cancelación de ruido es increíble. "
            "R5 (Calificación 1/5): Llegaron defectuosos, el auricular izquierdo no funciona. Pésimo servicio. "
            "R6 (Calificación 4/5): Buen producto por el precio, la batería es buena. "
            "R7 (Calificación 3/5): Sonido correcto, nada especial. El micrófono es regular. "
            "R8 (Calificación 5/5): Me encantan, el mejor producto que compré este año. "
            "R9 (Calificación 2/5): Incómodos para usar mucho tiempo, se caen al correr. "
            "R10 (Calificación 4/5): Excelente relación calidad precio, los recomiendo."
        ),
    },
    {
        "id": "doc-002",
        "title": "Ventas trimestrales AuraPods 2025",
        "text": (
            "Ventas de AuraPods en 2025 (unidades vendidas): Q1: 12000, Q2: 15500, Q3: 14200, Q4: 21800. "
            "Precio promedio de venta: USD 59.90 por unidad. Costo unitario: USD 38.50."
        ),
    },
    {
        "id": "doc-003",
        "title": "Competencia: SonicBuds y PulseAir",
        "text": (
            "SonicBuds: precio USD 79.00, calificación promedio 4.2/5, batería 8 horas. "
            "PulseAir: precio USD 49.00, calificación promedio 3.4/5, batería 5 horas. "
            "AuraPods: precio USD 59.90, batería 10 horas, cancelación de ruido activa."
        ),
    },
    {
        "id": "doc-004",
        "title": "Patrón Supervisor en LangGraph",
        "text": (
            "En la topología jerárquica con supervisor, un nodo central decide qué agente especialista "
            "interviene en cada turno mediante aristas condicionales y los especialistas devuelven el control "
            "al supervisor. Buenas prácticas: contador de pasos, criterio de suficiencia y contexto acotado."
        ),
    },
]
