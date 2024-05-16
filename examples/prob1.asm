section .text:
    move r0, #0         @ текущее число для проверки
    move r1, #0         @ сумма
    move r2, #1000      @ граница
    move r3, #3         @ делитель
    move r5, #5         @ делитель

    .loop:
        inc r0
        cmp r2, r0
        jz .end
        mod r6, r0, r3
        jz .sum
        mod r6, r0, r5
        jz .sum
        jmp .loop

    .end:
        halt

    .sum:
        add r1, r1, r0
        jmp .loop