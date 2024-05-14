section .data:
    hello: 123
    pointer: hello

section .text:
    load r0, hello
    load r1, (pointer)
    cmp r1, r0

    move r6, r1

    jnz .end
    inc r5

    .end:
    jmp .edtr
        add r1, r2, r3

    .edtr:
        halt