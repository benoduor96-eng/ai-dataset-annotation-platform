package com.benoduor.ingestion.controller;
import com.benoduor.ingestion.model.IngestionRequest;
import com.benoduor.ingestion.service.IngestionService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
@RestController @RequestMapping("/api/v1/ingestion") public class IngestionController {
 private final IngestionService service; public IngestionController(IngestionService service){this.service=service;}
 @PostMapping public ResponseEntity<?> ingest(@Valid @RequestBody IngestionRequest request){return ResponseEntity.accepted().body(Map.of("status","accepted","sequence",service.accept(request),"externalId",request.externalId()));}
 @GetMapping("/stats") public Map<String,Object> stats(){return Map.of("accepted",service.count());}
 @GetMapping("/health") public Map<String,String> health(){return Map.of("status","ok","service","java-ingestion");}
}
