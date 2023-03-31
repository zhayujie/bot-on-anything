
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    })
}

const conversationType = {
    DISPOSABLE: 1,
    STREAM: 1 << 1
}
function ConvState(wrapper, form, params) {
    this.id = generateUUID()
    this.form = form;
    this.wrapper = wrapper;
    this.backgroundColor = '#ffffff';
    this.parameters = params;
    this.scrollDown = function () {
        $(this.wrapper).find('#messages').stop().animate({ scrollTop: $(this.wrapper).find('#messages')[0].scrollHeight }, 600);
    }.bind(this);
};
ConvState.prototype.printAnswer = function (uuid, answer = '我是ChatGPT, 一个由OpenAI训练的大型语言模型, 我旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。输入 #清除记忆 可以开始新的话题探索。输入 画xx 可以为你画一张图片。我无法对事实性与实时性问题提供准确答复，请慎重对待回答。') {
    setTimeout(function () {
        var messageObj = $(this.wrapper).find(`#${uuid}`);
        answer = marked.parse(answer);
        messageObj.html(answer);
        messageObj.removeClass('typing').addClass('ready');
        this.scrollDown();
        $(this.wrapper).find(this.parameters.inputIdHashTagName).focus();
    }.bind(this), 500);
};

ConvState.prototype.updateAnswer = function (question, uuid) {
    setTimeout(function () {
        var socket = io('/chat');
        socket.connect('/chat');
        let timerId;
        var _this = this
        // 设置计时器，如果在规定的时间内没有接收到消息，则手动断开连接
        function setTimer() {
            timerId = setTimeout(() => {
                if (socket.connected) {
                    socket.disconnect();
                    handle_disconnect();
                }
            }, 60000);
        }
        function resetTimer() {
            clearTimeout(timerId);
            setTimer();
        }
        setTimer();
        var messageObj = $(this.wrapper).find(`#${uuid}`);
        function handle_disconnect() {
            messageObj.removeClass('typing').addClass('ready');
            _this.scrollDown();
            $(_this.wrapper).find(_this.parameters.inputIdHashTagName).focus();
        }
        this.scrollDown();
        socket.on('message', msg => {
            // 接收到消息时重置计时器
            resetTimer();
            if (msg.result)
                messageObj.html(msg.result + `<div class="typing_loader"></div></div>`);
            this.scrollDown();
        });
        socket.on('connect', msg => {
            socket.emit('message', { data: JSON.stringify(question) });
        });
        socket.on('disconnect', msg => {
            if (msg.result) {
                answer = marked.parse(msg.result);
                messageObj.html(answer);
            }
            handle_disconnect()
        });
    }.bind(this), 1000);
};
ConvState.prototype.sendMessage = function (msg) {
    var message = $('<div class="message from">' + msg + '</div>');
    $('button.submit').removeClass('glow');
    $(this.wrapper).find(this.parameters.inputIdHashTagName).focus();
    setTimeout(function () {
        $(this.wrapper).find("#messages").append(message);
        this.scrollDown();
    }.bind(this), 100);
    var uuid = generateUUID().toLowerCase();
    var messageObj = $(`<div class="message to typing" id="${uuid}"><div class="typing_loader"></div></div>`);
    setTimeout(function () {
        $(this.wrapper).find('#messages').append(messageObj);
        this.scrollDown();
    }.bind(this), 150);
    var _this = this
    var question = { "id": _this.id, "msg": msg }
    if (localConfig.conversationType == conversationType.STREAM)
        this.updateAnswer(question, uuid)
    else
        $.ajax({
            url: "./chat",
            type: "POST",
            timeout: 180000,
            data: JSON.stringify(question),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (data) {
                _this.printAnswer(uuid, data.result)
            },
            error: function (data) {
                console.log(data)
                _this.printAnswer(uuid, "网络故障，对话未送达")
            },
        })
};
(function ($) {
    $.fn.convform = function () {
        var wrapper = this;
        $(this).addClass('conv-form-wrapper');

        var parameters = $.extend(true, {}, {
            placeHolder: 'Type Here',
            typeInputUi: 'textarea',
            formIdName: 'convForm',
            inputIdName: 'userInput',
            buttonText: '▶'
        });

        //hides original form so users cant interact with it
        var form = $(wrapper).find('form').hide();

        var inputForm;
        parameters.inputIdHashTagName = '#' + parameters.inputIdName;
        inputForm = $('<div id="' + parameters.formIdName + '" class="convFormDynamic"><div class="options dragscroll"></div><textarea id="' + parameters.inputIdName + '" rows="1" placeholder="' + parameters.placeHolder + '" class="userInputDynamic"></textarea><button type="submit" class="submit">' + parameters.buttonText + '</button><span class="clear"></span></form>');

        //appends messages wrapper and newly created form with the spinner load
        $(wrapper).append('<div class="wrapper-messages"><div class="spinLoader"></div><div id="messages"></div></div>');
        $(wrapper).append(inputForm);

        var state = new ConvState(wrapper, form, parameters);
        // Bind checkbox values to ConvState object
        $('input[type="checkbox"]').change(function () {
            var key = $(this).attr('name');
            state[key] = $(this).is(':checked');
        });

        // Bind radio button values to ConvState object
        $('input[type="radio"]').change(function () {
            var key = $(this).attr('name');
            state[key] = $(this).val();
        });

        // Bind color input value to ConvState object
        $('#backgroundColor').change(function () {
            state["backgroundColor"] = $(this).val();
        });

        //prints first contact
        $.when($('div.spinLoader').addClass('hidden')).done(function () {
            var uuid = generateUUID()
            var messageObj = $(`<div class="message to typing" id="${uuid}"><div class="typing_loader"></div></div>`);
            $(state.wrapper).find('#messages').append(messageObj);
            state.scrollDown();
            state.printAnswer(uuid = uuid);
        });

        //binds enter to send message
        $(inputForm).find(parameters.inputIdHashTagName).keypress(function (e) {
            if (e.which == 13) {
                var input = $(this).val();
                e.preventDefault();
                if (input.trim() != '' && !state.wrapper.find(parameters.inputIdHashTagName).hasClass("error")) {
                    $(parameters.inputIdHashTagName).val("");
                    state.sendMessage(input);
                } else {
                    $(state.wrapper).find(parameters.inputIdHashTagName).focus();
                }
            }
            autosize.update($(state.wrapper).find(parameters.inputIdHashTagName));
        })
        $(inputForm).find(parameters.inputIdHashTagName).on('input', function (e) {
            if ($(this).val().length > 0) {
                $('button.submit').addClass('glow');
            } else {
                $('button.submit').removeClass('glow');
            }
        });

        $(inputForm).find('button.submit').click(function (e) {
            var input = $(state.wrapper).find(parameters.inputIdHashTagName).val();
            e.preventDefault();
            if (input.trim() != '' && !state.wrapper.find(parameters.inputIdHashTagName).hasClass("error")) {
                $(parameters.inputIdHashTagName).val("");
                state.sendMessage(input);
            } else {
                $(state.wrapper).find(parameters.inputIdHashTagName).focus();
            }
            autosize.update($(state.wrapper).find(parameters.inputIdHashTagName));
        });

        if (typeof autosize == 'function') {
            $textarea = $(state.wrapper).find(parameters.inputIdHashTagName);
            autosize($textarea);
        }

        return state;
    }
})(jQuery);
