li  t0, 0x1003
ld  t1, 0(t0)         
li  t0, 0x1003
sd  t1, 0(t0)          
li  t0, 0xfffffffffffff000
ld  t1, 0(t0)
li  t0, 0xfffffffffffff000
sd  t1, 0(t0)
li  t0, 0xfffffffffffff000
jr  t0                 
li  t0, 0x40000000     
jr  t0                
li  t0, 0x40000000
ld  t1, 0(t0)
li  t0, 0x40000000
sd  t1, 0(t0)
ecall 
ebreak
j done
