section .data:
section .text:
    ei
    .loop:
        jmp .loop

    .int1:
        in r1, 0
        cmp r1, #0
        jz .end
        out r1, 1
        iret

    .end:
        halt