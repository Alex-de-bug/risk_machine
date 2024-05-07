section .text:
    move r0, #1         @ текущее число для проверки
    move r1, #0         @ сумма
    move r2, #1001      @ граница
    move r3, #3         @ делитель
    move r5, #5         @ делитель

    .loop:
        mod r6, r0, r3
        jz .sum
        mod r6, r0, r5
        jz .sum
        inc r0
        cmp r2, r0
        jz .end
        jmp .loop

    .end:
        out r1, 1
        halt

    .sum:
        add r1, r1, r0
        jmp .loop