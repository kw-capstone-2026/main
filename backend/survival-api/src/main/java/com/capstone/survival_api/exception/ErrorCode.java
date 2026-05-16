package com.capstone.survival_api.exception;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    // Auth
    INVALID_EMAIL(HttpStatus.BAD_REQUEST, "INVALID_EMAIL", "이메일 형식이 올바르지 않습니다."),
    INVALID_PASSWORD(HttpStatus.BAD_REQUEST, "INVALID_PASSWORD", "비밀번호는 8자 이상이어야 합니다."),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "DUPLICATE_EMAIL", "이미 가입된 이메일입니다."),
    INVALID_CREDENTIALS(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "USER_NOT_FOUND", "존재하지 않는 계정입니다."),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "토큰이 없거나 만료되었습니다."),

    // Block
    BLOCK_NOT_FOUND(HttpStatus.NOT_FOUND, "BLOCK_NOT_FOUND", "존재하지 않는 블록입니다."),
    INVALID_CSI_RANGE(HttpStatus.BAD_REQUEST, "INVALID_CSI_RANGE", "csiMin이 csiMax보다 클 수 없습니다."),

    // Prediction
    PREDICTION_NOT_FOUND(HttpStatus.NOT_FOUND, "PREDICTION_NOT_FOUND", "해당 블록의 예측 결과가 없습니다."),

    // Industry
    INDUSTRY_STATS_NOT_FOUND(HttpStatus.NOT_FOUND, "INDUSTRY_STATS_NOT_FOUND", "해당 블록의 업종 통계가 없습니다."),
    INVALID_MONTHS(HttpStatus.BAD_REQUEST, "INVALID_MONTHS", "months는 1 이상 60 이하이어야 합니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;
}
