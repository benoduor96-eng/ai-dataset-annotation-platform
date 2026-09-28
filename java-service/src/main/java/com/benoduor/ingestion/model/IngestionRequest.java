package com.benoduor.ingestion.model;
import jakarta.validation.constraints.NotBlank;
public record IngestionRequest(@NotBlank String datasetId, @NotBlank String externalId, Object payload) {}
