<pre>
prc = SubProcess('cat')
test_text = [
	'123\n',
	'text\n',
	'ololo\n',
]

prc.pipe.stdin.write(''.join(test_text))

from time import sleep
sleep(1)

assert prc.stdout == ''.join(test_text)
</pre>
