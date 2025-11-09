<script>
    var numble = new Array(75);
    var numblig = new Array(50);
</script>

<style>
    #bubblid {
        background-color: transparent;
        height: 100%;
        width: 100%;
        float: left;
        position: fixed;
    }
    .bubble {
        image-rendering: pixelated;
        position: absolute;
        top: 150vh;
        animation: 3s linear 1 both normal rise,
            0.5s linear infinite alternate sway;
        width: 10vmax;
        height: 10vmax;
    }
    .bubblig {
        image-rendering: pixelated;
        position: absolute;
        top: 150vh;
        animation: 2.5s linear 1 both normal rise,
            0.5s linear infinite alternate sway;
        width: 30vmax;
        height: 30vmax;
    }
    @keyframes rise {
        from {
            top: 150vh;
        }
        to {
            top: -80vh;
        }
    }
    @keyframes sway {
        from {
            transform: translate(0%);
        }
        to {
            transform: translate(10%);
        }
    }
</style>

<div id="bubblid">
    {#each numblig as _, numb}
        <img class="bubblig" src="/assets/Sprite-Bubble.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()*0.5}s">
        <img class="bubblig" src="/assets/Sprite-Bubble2.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()}s">
        <img class="bubblig" src="/assets/Sprite-Bubble3.gif" alt="bubble!" style="left: {Math.random()*110-5}%; animation-delay:{numb*.03+1}s,{Math.random()}s">
    {/each}
    {#each numble as _, numb}
        <img class="bubble" src="/assets/Sprite-Bubble.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
        <img class="bubble" src="/assets/Sprite-Bubble2.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
        <img class="bubble" src="/assets/Sprite-Bubble3.gif" alt="bubble!" style="transform: scale({Math.random()*2+0.5}); left: {Math.random()*110-5}%; animation-delay:{numb*.04}s,{Math.random()}s">
    {/each}
</div>