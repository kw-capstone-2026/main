package com.capstone.survival_api.exception;

import lombok.Builder;
import lombok.Getter;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AppException.class)
    public ResponseEntity<ErrorResponse> handleAppException(AppException e) {
        ErrorCode code = e.getErrorCode();
        return ResponseEntity
                .status(code.getStatus())
                .body(ErrorResponse.of(code));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getDefaultMessage())
                .findFirst()
                .orElse("요청 값이 올바르지 않습니다.");
        return ResponseEntity
                .badRequest()
                .body(new ErrorResponse(400, "INVALID_INPUT", message));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception e) {
        return ResponseEntity
                .internalServerError()
                .body(new ErrorResponse(500, "INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다."));
    }

    @Getter
    @Builder
    public static class ErrorResponse {
        private final int status;
        private final String code;
        private final String message;

        public ErrorResponse(int status, String code, String message) {
            this.status = status;
            this.code = code;
            this.message = message;
        }

        public static ErrorResponse of(ErrorCode errorCode) {
            return new ErrorResponse(
                    errorCode.getStatus().value(),
                    errorCode.getCode(),
                    errorCode.getMessage()
            );
        }
    }
}
