package com.benoduor.ingestion.service;
import com.benoduor.ingestion.model.IngestionRequest;
import org.springframework.stereotype.Service;
import java.util.concurrent.atomic.AtomicLong;
@Service public class IngestionService { private final AtomicLong accepted=new AtomicLong(); public long accept(IngestionRequest request){return accepted.incrementAndGet();} public long count(){return accepted.get();} }
