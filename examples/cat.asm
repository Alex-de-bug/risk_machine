section .text:
    ei
    .loop:
        jmp .loop

    .end:
        halt

.int1:
    in r1, 0
    move r2, #48  @ char(48) == 0
    cmp r1, r2
    jz .end
    out r1, 1
    iret