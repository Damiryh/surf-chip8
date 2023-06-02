start:
    ld @0, 100
    sub @0, 1
    se @0, 0
    jp [start]
end:
    jp [end]
