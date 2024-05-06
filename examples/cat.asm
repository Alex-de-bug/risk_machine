section .rodata:
section .text:
    ei
    .loop:
        jmp .loop

    .end:
        halt

.int1:
    in r1, 0
    cmp r1, #0
    jz .end
    out r1, 1
    iret